import pycallgraph
import cherrypy
from cherrypy.lib import file_generator


__version__ = "1.0.0"
__author__ = "Noon Silk"

class CallGraphInfo:
    """
        Maps some routes for looking at all graphs. Bind this to something like:
            /graphs

        then view it by browsing to, unsurprisingly, /graphs. You'll of course neeed
        an appropriate config in cherrypy.
    """

    image_file = ""

    # Hardcoded for now. Probably can just overload this
    # to be loaded from some template.

    html = """
        <html>
            <head>
                <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js"></script>
            </head>
            <body>
                <script>
                    var go = true;

                    function beginTimer () {
                        setTimeout( function(){ refreshImage(); }, 5 * 1000);
                    }

                    function refreshImage () {
                        if( !go ){
                            return;
                        }

                        var d = new Date();
                        var m  = d.getTime();
                        $('#img').attr('src', 'render?include=' + $('#include').val() + '&exclude=' + $('#exclude').val() + '&' + m);
                        beginTimer();
                    }

                    $(document).ready(function(){ beginTimer(); });
                </script>

                <table>
                <tr>
                    <td>Include</td>
                    <td> <input type='text' id='include' value='%(include)s' /> </td>
                </tr>
                <tr>
                    <td>Exclude</td>
                    <td> <input type='text' id='exclude' value='%(exclude)s' /> </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <input id='stop' type='button' value='Stop' onclick='go = false; $("#stop").hide(); $("#start").show();' />
                        <input id='start' type='button' value="Start" onclick='go = true; $("#start").hide(); $("#stop").show(); beginTimer();' 
                            style='display: none'; />
                    </td>
                </table>

                <img id='img' src="render" />
            </body>
        </html>
    """
    base_include = []
    base_exclude = []
     
    last_include = []
    last_exclude = []

    started = False


    def __init__ (self, image_file, include, exclude): # {{{
        self.image_file = image_file
        self.html = self.html % { 'image': image_file,
                'include': ','.join(include), 'exclude': ','.join(exclude) }

        self.base_include += include
        self.base_exclude += exclude

        self.last_include = include
        self.last_exclude = exclude
    # }}}


    def filter_func (self, include=None, exclude=None): # {{{
        """
            Either uses the default include/excludes, or uses the ones
            passed in. If passed in, it sets some state to make sure we
            know if they have changed.
        """

        inc = self.base_include
        exc = self.base_exclude

        if include:
            self.last_include = include
            inc = include

        if exclude:
            self.last_exclude = exclude
            exc = exclude

        return pycallgraph.GlobbingFilter(include=inc, exclude=exc)
    # }}}


    @cherrypy.expose
    def index (self): # {{{
        """
            Returns a page on which to control the graph. If the trace hasn't
            been started already, it starts it.
        """

        if not self.started:
            self.start()

        return self.html
    # }}}


    @cherrypy.expose
    def stop (self): # {{{
        pycallgraph.stop_trace()
        self.started = False
    # }}}


    @cherrypy.expose
    def start (self): # {{{
        self.started = True
        pycallgraph.start_trace(filter_func = self.filter_func())
    # }}}


    @cherrypy.expose
    def render (self, include=None, exclude=None, **kwargs): # {{{
        """
            Actually returns an image (as png), and will reset the trace if the
            include or exclude parameters are different.
        """
        
        inc = self.last_include
        exc = self.last_exclude

        if include or include == "":
            inc = include.split(',')

        if exclude or exclude == "":
            exc = exclude.split(',')

        if inc != self.last_include or exc != self.last_exclude:
            # New trace, resetting the old one.

            pycallgraph.stop_trace()
            pycallgraph.start_trace(filter_func = self.filter_func(inc, exc), reset=True)

        pycallgraph.make_dot_graph("." + self.image_file, stop=False)

        cherrypy.response.headers['Content-Type'] = "image/png"
        f = open("." + self.image_file, "r+b")
        return f.read()
    # }}}
