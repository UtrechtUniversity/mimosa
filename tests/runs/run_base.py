from mimosa import MIMOSA, load_params

params = load_params()  # (1)!

model1 = MIMOSA(params)  # (2)!
model1.solve()  # (3)!

model1.save("run1")  # (4)!
