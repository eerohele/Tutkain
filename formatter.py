def format_out(out):
    return '\n'.join(map(lambda line: ';; {}'.format(line), out.splitlines()))


def format(message):
    if 'value' in message:
        return message['value'] + '\n'
    if 'nrepl.middleware.caught/throwable' in message:
        return message.get('nrepl.middleware.caught/throwable') + '\n'
    if 'out' in message:
        return format_out(message['out']) + '\n'
    if 'append' in message:
        return message['append']
    if 'err' in message:
        return format_out(message.get('err')) + '\n'
    if 'in' in message:
        return format_out('=> {}'.format(message['in'])) + '\n'
