from .util import ViewTestCase


class TestZapCommas(ViewTestCase):
    def test_find_next(self):
        self.set_view_content("")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_zap_commas")
        self.assertEquals("", self.view_content())

        self.set_view_content("{:a :b, :c :d} {:d :e, :f :g} {:h :i, :j :l}")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_zap_commas")
        self.assertEquals("{:a :b :c :d} {:d :e :f :g} {:h :i :j :l}", self.view_content())

        self.set_view_content("{:a :b, :c :d} {:d :e, :f :g} {:h :i, :j :l}")
        self.set_selections((0, 14))
        self.view.run_command("tutkain_zap_commas")
        self.assertEquals("{:a :b :c :d} {:d :e, :f :g} {:h :i, :j :l}", self.view_content())

        self.set_view_content("{:a :b, :c :d} {:d :e, :f :g} {:h :i, :j :l}")
        self.set_selections((0, 14), (31, 45))
        self.view.run_command("tutkain_zap_commas")
        self.assertEquals("{:a :b :c :d} {:d :e, :f :g} {:h :i :j :l}", self.view_content())
