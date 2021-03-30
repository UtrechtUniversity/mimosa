from model.mimosa import MIMOSA

from model.common.config import params

model1 = MIMOSA(params)
model1.solve()
model1.plot()
model1.save()
