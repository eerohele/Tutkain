import os
import sublime

from . import forms
from . import namespace
from . import sexp


def current(view, point):
    for s in sexp.walk_outward(view, point, edge=True):
        head = forms.find_next(view, s.open.end())

        if view.match_selector(head.begin(), 'meta.deftest.clojure'):
            form = forms.seek_forward(
                      view,
                      head.end(),
                      lambda form: view.match_selector(form.begin(), 'meta.test-var.clojure')
            )

            if form:
                return view.substr(form)


def add_annotation(response):
    args = {
        'reference': response['expected'],
        'actual': response['actual']
    }

    return '''
    <a style="font-size: 0.8rem"
       href='{}'>{}</a>
    '''.format(
        sublime.command_url('tutkain_open_diff_window', args=args),
        'diff' if response.get('type', 'fail') == 'fail' else 'show'
    )


def region_key(view, result_type):
    return '{}:{}'.format(view.file_name(), result_type)


def regions(view, result_type):
    return view.get_regions(region_key(view, result_type))


def add_markers(view, session, response):
    if 'status' not in response:
        view.run_command('tutkain_clear_test_markers')

    results = {'fail': {}, 'error': {}, 'pass': {}}

    if 'fail' in response:
        for result in response['fail']:
            line = result['line'] - 1
            point = view.text_point(line, 0)

            results['fail'][line] = {
                'type': result['type'],
                'region': sublime.Region(point, point),
                'expected': result['expected'],
                'actual': result['actual']
            }

    if 'error' in response:
        for result in response['error']:
            line = result['var-meta']['line'] - 1
            column = result['var-meta']['column'] - 1
            point = view.text_point(line, column)

            results['error'][line] = {
                'type': result['type'],
                'region': forms.find_next(view, point),
                'expected': result['expected'],
                'actual': result['actual']
            }

    if 'pass' in response:
        for result in response['pass']:
            line = result['line'] - 1
            point = view.text_point(line, 0)

            # Only add pass for line if there's no fail for the same line.
            if line not in results['fail']:
                results['pass'][line] = {
                    'type': result['type'],
                    'region': sublime.Region(point, point)
                }

        passes = results['pass'].values()
        if passes:
            view.add_regions(
                region_key(view, 'passes'),
                [p['region'] for p in passes],
                scope='region.greenish',
                icon='circle'
            )

        failures = results['fail'].values()
        if failures:
            view.add_regions(
                region_key(view, 'failures'),
                [f['region'] for f in failures],
                scope='region.redish',
                icon='circle',
                annotations=[add_annotation(f) for f in failures]
            )

        errors = results['error'].values()
        if errors:
            view.add_regions(
                region_key(view, 'errors'),
                [e['region'] for e in errors],
                scope='region.orangish',
                icon='circle',
                annotation_color='orange',
                annotations=[add_annotation(e) for e in errors],
                flags=sublime.DRAW_NO_FILL
            )


def evaluate_view(view, session, response, test_vars):
    if response.get('status') == ['done']:
        op = {'op': 'load-file',
              'file': view.substr(sublime.Region(0, view.size()))}

        file_path = view.file_name()

        if file_path:
            file = os.path.basename(file_path)
            op['file-name'] = file
            op['file-path'] = file_path
        else:
            file = 'NO_SOURCE_FILE'

        session.send(
            op,
            handler=lambda response: run_tests(view, session, response, file, file_path, test_vars)
        )


def run_tests(view, session, response, file, file_path, test_vars):
    if response.get('status') == ['eval-error']:
        session.denounce(response)
    elif response.get('status') == ['done']:
        if not session.is_denounced(response):
            if int(sublime.version()) >= 4073 and session.supports('tutkain/test'):
                def handler(response):
                    session.output(response)
                    add_markers(view, session, response)

                op = {
                    'op': 'tutkain/test',
                    'ns': namespace.find_declaration(view),
                    'file': file
                }

                if test_vars:
                    op['vars'] = test_vars

                session.send(op, handler=handler)
            else:
                # For nREPL < 0.8 compatibility
                session.send(
                    {'op': 'eval',
                     'code': '''
(let [report clojure.test/report]
  (with-redefs [clojure.test/report (fn [event] (report (assoc event :file "%s")))]
    ((requiring-resolve \'clojure.test/run-tests))))
                     ''' % file,
                     'file': file_path}
                )
    elif response.get('value'):
        pass
    else:
        session.output(response)


def run(view, session, test_vars=[]):
    if session is None:
        view.window().status_message('ERR: Not connected to a REPL.')
    else:
        session.send(
            {'op': 'eval',
             'code': '''(->> (ns-publics *ns*)
                             (filter (fn [[_ v]] (-> v meta :test)))
                             (run! (fn [[sym _]] (ns-unmap *ns* sym))))''',
             'file': view.file_name()},
            handler=lambda response: evaluate_view(view, session, response, test_vars)
        )
