# interview.py
#
# Copyright (c) 2008 Jack Moffitt <metajack@gmail.com>
#     and Siddhi <http://siddhi.blogspot.com/2007/07/generating-sentences-using-markov.html>
#
# Main markov chain generator code and twisted.web Resource class.
#
# This code was derived from code originally published by Siddhi.
#
# This file is part of interview.
#
# Interview is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Interview is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import random
import time

from glob import glob

from twisted.web import resource

from Cheetah.Template import Template

def getLines(filename):
    return [line[0:-1] for line in open(filename).readlines()]

def getWords(lines):
    words = []
    for line in lines:
	words.extend(line.split())
    #words = [w.lower() for w in words]
    return words

def createProbabilityHash(words):
    numWords = len(words)
    wordCount = {}
    for word in words:
	if wordCount.has_key(word):
	    wordCount[word] += 1
	else:
	    wordCount[word] = 1
 
    for word in wordCount.keys():
	wordCount[word] /= 1.0 * numWords
    
    return wordCount

def getRandomWord(wordCount):
    randomValue = random.random()
    cumulative = 0.0
    for word in wordCount:
	cumulative += wordCount[word]
	if cumulative > randomValue:
	    return word

def appendWordToMap(word_map, previous, word):
    if word_map.has_key(previous):
	word_map[previous].append(word)
    else:
	word_map[previous] = [word]


def setup(filename):
    words = getWords(getLines(filename))
    word_maps = ({}, {}, {})

    pos = 0

    for word in words[1:]:
	pos += 1

	# do order 1
	previous = words[pos - 1]
	appendWordToMap(word_maps[0], previous, word)

	# do order 2
	if pos > 1:
	    previous = (words[pos - 2], words[pos - 1])
	    appendWordToMap(word_maps[1], previous, word)

	# do order 3
	if pos > 2:
	    previous = (words[pos - 3], words[pos - 2], words[pos - 1])
	    appendWordToMap(word_maps[2], previous, word)


    for word_map in word_maps:
	for word in word_map.keys():
	    probabilityHash = createProbabilityHash(word_map[word])
	    word_map[word] = probabilityHash

    return words, word_maps

def getNextWord(words, word_maps, order, previous):
    max_order = 3
    if previous[0] == None:
	max_order = 2
    if previous[1] == None:
	max_order = 1
    
    max_order = min(order, max_order)

    for o in range(max_order, 0, -1):
	if o == 3:
	    prev = previous
	elif o == 2:
	    prev = tuple(previous[1:])
	else:
	    prev = previous[-1]

	if word_maps[o-1].has_key(prev):
	    return getRandomWord(word_maps[o-1][prev])
	  
    # no match found, return a random word
    return words[random.randint(0, len(words) - 1)]
    

def make_talk(words, word_maps, state=None, num_words=100, order=2):
    # the starting state
    previous = state or (None, None, words[random.randint(0, len(words)-1)])

    if previous[0]:
	text = list(previous[:])
    elif previous[1]:
	text = list(previous[1:])
    else:
	text = [previous[2]]

    i = 0
    while i < num_words or (i >= num_words and text[-1][-1] != '.'):
	word = getNextWord(words, word_maps, order, previous)
	text.append(word)
	i += 1
	previous = (previous[1], previous[2], word)
	

    return ' '.join(text)

NAMES = {
    'palin': {'short': 'Palin', 'long': 'Sarah Palin'},
    'mccain': {'short': 'McCain', 'long': 'John McCain'},
    'biden': {'short': 'Biden', 'long': 'Joe Biden'},
    'obama': {'short': 'Obama', 'long': 'Barak Obama'}
}

class Interview(resource.Resource):
    isLeaf = False

    perm_re = re.compile('^c(\d+)q(\d+)s(\d+)-(.+)$')
    action_re = re.compile('^([rn])(\d+)$')

    def __init__(self, persona):
	resource.Resource.__init__(self)

	self.persona = persona

	self.reload()

    def getChild(self, name, request):
	perm_match = self.perm_re.match(name)
	action_match = self.action_re.match(name)
	if name == '' or perm_match or action_match:
	    return self

	return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
	prefix = None
	last = str(request.URLPath()).split('/')
	if len(last) > 0:
	    prefix = '/'.join(last[:-1])
	    last = last[-1]
	else:
	    prefix = 'http://interview%s.com' % self.persona
	    last = ''

	# decode permalink or action from last
	corpus = None
	question = None
	state = None
	seed = None
	repeatq = True

	perm_match = self.perm_re.match(last)
	action_match = self.action_re.match(last)
	if perm_match:
	    corpus = int(perm_match.group(1))
	    question = int(perm_match.group(2))
	    state = int(perm_match.group(3))
	    seed = int(perm_match.group(4), 16)
	elif action_match:
	    action = action_match.group(1)
	    question = int(action_match.group(2))
	    if action == 'r':
		repeatq = True
	    elif action == 'n':
		repeatq = False
	elif last != '':
	    prefix += '/' + last
	    
	if seed is None:
	    seed = int(time.time() * 1000)
	random.seed(seed)

	# pregenerate random numbers
	q_rand = random.random()
	s_rand = random.random()

	# choose corpus
	if corpus is None:
	    corpus = len(self.corpus) - 1
	words = self.corpus[corpus]['words']
	word_maps = self.corpus[corpus]['word_maps']

	# choose question
	num_q = len(self.config)
	if question is None:
	    question = int(round(q_rand * (num_q - 1)))
	elif question >= 0 and not repeatq:
	    new_q = int(round(q_rand * (num_q - 1)))
	    if new_q == question:
		question = (new_q + 1) % num_q
	    else:
		question = new_q

	# choose starting state
	num_states = len(self.config[question]['state'])
	state = int(round(s_rand * (num_states - 1)))

	# fill out the template
	self.template.question = self.config[question]['question']
	self.template.answer = make_talk(words,
					 word_maps,
					 self.config[question]['state'][state])
	self.template.permalink = '%s/c%dq%ds%d-%x' % \
	    (prefix, corpus, question, state, seed)
	self.template.question_id = question
	self.template.prefix = prefix
	
	return str(self.template)

    def reload(self):
	self.corpus = []
	texts = sorted(glob("%s-*.txt" % self.persona))
	for t in texts:
	    w, wm = setup(t)
	    self.corpus.append({'words': w, 'word_maps': wm})
	

	self.config = eval(open(self.persona + '.config').read())

	self.template = Template(file='%s.html' % self.persona)
	
	self.template.title = 'Interview%s.com' % NAMES[self.persona]['short']
	self.template.name = NAMES[self.persona]['long']
	


if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 5:
	print "usage: %s PERSONA [START1 [START2 [START3]]]" % sys.argv[0]
	sys.exit(1)

    persona = sys.argv[1]

    order = 2
    if persona[-1] in ('1', '2', '3'):
	order = int(persona[-1])
	persona = persona[:-1]

    text = sorted(glob("%s-*.txt" % persona))[-1]
    w, wm = setup(text)

    start = sys.argv[2:]
    if len(start) == 1:
	start = (None, None, start[0])
    elif len(start) == 2:
	start = (None, start[0], start[1])
    else:
	start = tuple(start)

    print make_talk(w, wm, start, order=order)
