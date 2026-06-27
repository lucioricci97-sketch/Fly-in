"""Allow ``python -m src ...`` to run the program."""
from .main import main

raise SystemExit(main())
