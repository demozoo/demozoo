"""
A python-markdown extension to treat newlines as hard breaks; like
StackOverflow and GitHub flavored Markdown do.

"""
import markdown


BR_RE = r'\n'

class Nl2BrExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        br_tag = markdown.inlinepatterns.SubstituteTagPattern(BR_RE, 'br')
        md.inlinePatterns.add('nl', br_tag, '_end')


def makeExtension(configs=None):
    return Nl2BrExtension(configs)
