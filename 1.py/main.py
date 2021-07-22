###-- 1.	Write python code to flatten and evaluate a deep tree in NLP --- ##


from nltk.tree import Tree

def flatten_childtrees(trees):
    children = []

    for t in trees:
        if t.height() < 3:
            children.extend(t.pos())
        elif t.height() == 3:
            children.append(Tree(t.label(), t.pos()))
        else:
            children.extend(flatten_childtrees([c for c in t]))
    return children


def flatten_deeptree(tree):
    return Tree(tree.label(),flatten_childtrees([c for c in tree]))

import nltk
nltk.download('treebank')

from nltk.corpus import treebank
#from transforms import flatten_deeptree

print("Deep Tree : \n", treebank.parsed_sents()[0])
print("\n Flattened Tree : \n", flatten_deeptree(treebank.parsed_sents()[0]))

from nltk.corpus import treebank

# from transforms import flatten_deeptree


from nltk.tree import Tree

print("Height : ", Tree('NNP', ['Pierre']).height())

print("\nHeight : ", Tree('NP', [Tree('NNP', ['Pierre']), Tree('NNP', ['Vinken'])]).height())