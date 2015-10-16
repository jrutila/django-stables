from django import template
from django.template.base import Node, NodeList, TemplateSyntaxError
register = template.Library()

from django.core.urlresolvers import reverse

@register.simple_tag
def active(request, pattern):
    if reverse(pattern) in request.path:
        return 'class="active"'
    return ''

def do_ifactive(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError("%r takes two arguments" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])
    return IfActiveNode(val1, val2, nodelist_true, nodelist_false, negate)

@register.tag
def ifactive(parser, token):
    """
    Outputs the contents of the block if the two arguments equal each other.

    Examples::

        {% ifactive request "home" %}
            ...
        {% endifactive %}

    """
    return do_ifactive(parser, token, False)

@register.tag
def ifnotactive(parser, token):
    """
    Outputs the contents of the block if the two arguments equal each other.

    Examples::

        {% ifnotactive request "home" %}
            ...
        {% endifnotactive %}

    """
    return do_ifactive(parser, token, True)

class IfActiveNode(Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = var1, var2
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfActiveNode>"

    def render(self, context):
        val1 = self.var1.resolve(context, True)
        val2 = self.var2.resolve(context, True)
        is_active = reverse(val2) in val1.path
        if (not self.negate and is_active) or (self.negate and not is_active):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)
