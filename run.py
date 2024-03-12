import logging
import logging.handlers

handler = logging.handlers.WatchedFileHandler("mainlog.log")
handler.setFormatter(
    logging.Formatter("[%(levelname)s, %(asctime)s] %(name)s - %(message)s")
)
root = logging.getLogger()
root.setLevel("INFO")
root.addHandler(handler)

from mimosa import MIMOSA, load_params

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve()
model1.save("run1")
