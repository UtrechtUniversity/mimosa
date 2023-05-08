from model.mimosa import MIMOSA

from model.common.config import parseconfig

params = parseconfig.load_params()

model1 = MIMOSA(params)
model1.solve()
model1.save("run_filename")
# model1.plot(filename="plot")
