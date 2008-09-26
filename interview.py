import random
import time

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
    random.seed(time.time())
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

    text = [previous[-1]]

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
    isLeaf = True

    def __init__(self, persona):
	resource.Resource.__init__(self)

	self.words, self.word_maps = setup(persona + '.txt')
	self.config = eval(open(persona + '.config').read())

	self.template = Template(file='interview.html')
	
	self.template.title = 'Interview%s.com' % NAMES[persona]['short']
	self.template.name = NAMES[persona]['long']


    def render_GET(self, request):
	self.template.question = self.config[0]['question']
	self.template.answer = make_talk(self.words,
					 self.word_maps,
					 self.config[0]['state'][0])
	return str(self.template)


if __name__ == '__main__':
    words, word_maps = setup()

    print make_talk(words, word_maps)
