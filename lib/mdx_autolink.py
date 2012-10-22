# -*- coding: utf-8 -*-

"""
ABOUT

Auto links conversion for Markdown (http://gitorious.org/python-markdown).

You should place this snippet as file 'mdx_autolink.py' to
some dir in PYTHON_PATH, as described in docs here:
http://www.freewisdom.org/projects/python-markdown/Using_as_a_Module

LICENSE

Copyright 2009 Alexey Kinyov <rudi@05bit.com>. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY ALEXEY KINYOV ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ALEXEY KINYOV OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Alexey Kinyov.

"""

import re
import markdown

reflink_re = re.compile('^\s*\[[^\[\]]+\]:.+$')
link_re = re.compile('(\s+\(?|^)((http|ftp|https)://[-\w\#$%&~/.;:=,?@+]+)', re.IGNORECASE)

class AutoLinkPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        new_lines = []
        for line in lines:
            if reflink_re.match(line):
                new_lines.append(line)
            else:
                new_lines.append(link_re.sub(r'\1<a href="\2" target="_blank">\2</a>', line))
        return new_lines

class AutoLinkExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('autolink', AutoLinkPreprocessor(md), "_begin")

def makeExtension(configs=None):
    return AutoLinkExtension(configs=configs)