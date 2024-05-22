import logging
import logging.handlers

from mimosa import MIMOSA, load_params

handler = logging.handlers.WatchedFileHandler("mainlog.log")
handler.setFormatter(
    logging.Formatter("[%(levelname)s, %(asctime)s] %(name)s - %(message)s")
)
root = logging.getLogger()
root.setLevel("INFO")
root.addHandler(handler)

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve(verbose=False)  # (1)!
model1.save("run1_logged")
