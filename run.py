from model.mimosa import MIMOSA

from model.common.config import parseconfig

model1 = MIMOSA(parseconfig.params)
model1.solve()
model1.save()
model1.plot(filename="result")
