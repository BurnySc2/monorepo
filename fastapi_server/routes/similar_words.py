import random

# import nltk
from litestar import Controller, get
from nltk.corpus import wordnet as wn  # pyre-fixme[21]
from nltk.corpus.reader.wordnet import Synset  # pyre-fixme[21]

# nltk.download("wordnet")

# dog: Synset = wn.synset("dog.n.01")
# print(dog.hypernyms())
# print(dog.hyponyms())
# print(dog.member_holonyms())
# print(dog.root_hypernyms())
# print(wn.synset("dog.n.01").lowest_common_hypernyms(wn.synset("cat.n.01")))
# print(dog.similar_tos())
# # print(dog.jcn_similarity(wn.synset("cat.n.01")))
# # print(dog.lin_similarity(wn.synset("cat.n.01")))
# # print(dog.res_similarity(wn.synset("cat.n.01")))
# print(dog.wup_similarity(wn.synset("cat.n.01")))
# print(dog.wup_similarity(wn.synset("math.n.01")))
# print(dog.path_similarity(wn.synset("cat.n.01"))) # 0-1
# print(dog.path_similarity(wn.synset("math.n.01"))) # 0-1

# nouns = list(wn.all_synsets("n"))
# nouns_similar = sorted(nouns, key=lambda x: dog.wup_similarity(x), reverse=True)
# for s in nouns_similar[:30]:
#     print(s, dog.wup_similarity(s), s.definition())

# nouns_similar2 = sorted(nouns, key=lambda x: dog.path_similarity(x), reverse=True)
# for s in nouns_similar2[:30]:
#     print(s, dog.path_similarity(s), s.definition())

# for s in list(wn.all_synsets("n", lang="eng"))[:10]:
#     print(s, s.definition())


class MyWordsRoute(Controller):
    path = "/words"

    # pyre-fixme[11]
    nouns_cache: list[Synset] | None = None

    @property
    def nouns(self) -> list[Synset]:
        if self.nouns_cache is None:
            self.nouns_cache = list(wn.all_synsets("n", lang="eng"))
        return self.nouns_cache

    async def _get_random_nouns(self, number: int = 30) -> str:
        words = [s.name().split(".")[0] for s in random.choices(self.nouns, k=number)]
        return "\n".join(words)

    @get("/")
    async def index(self) -> str:
        # TODO Make and return index.html
        return "Hello world!"

    @get("/random_noun")
    async def get_random_noun(self) -> str:
        return await self._get_random_nouns(1)

    @get("/random_nouns")
    async def get_random_nouns_30(self, number: int = 30) -> str:
        return await self._get_random_nouns(30)

    @get("/random_nouns/{number:int}")
    async def get_random_nouns(self, number: int = 30) -> str:
        number = max(1, min(100, number))
        return await self._get_random_nouns(number)

    # TODO Api endpoint to get similar words to given noun (show similarity and their definition)
    # TODO restrict similarity level (0-1)
