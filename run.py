from mimosa.mimosa import MIMOSA

from mimosa.common.config import parseconfig

params = parseconfig.load_params()
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve()
model1.save("run1")
