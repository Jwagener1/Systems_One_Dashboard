"""Application entry point.

This module stitches together the model, service, view‑model and
view layers to create a running Dash application.  It instantiates
each component and injects dependencies via the constructor, making
the wiring explicit and testable.

Usage:
    $ python app.py
"""

from __future__ import annotations

import logging

from models.data_model import DataModel
from services.data_service import DataService
from viewmodels.data_viewmodel import DataViewModel
from views.dash_view import create_app
from utils import config


def main() -> None:
    """Create and run the Dash application.

    This function should remain minimal, performing only the
    composition of the different layers.  Business logic belongs
    inside the view‑model or service classes.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialise the model that knows how to load and represent data.
    data_model = DataModel()
    # Service layer that could wrap database/API logic.  For now it
    # simply delegates to the model, but its presence demonstrates
    # SOLID dependency inversion – upper layers depend on abstractions.
    data_service = DataService(model=data_model)
    # ViewModel orchestrates application state and prepares data for
    # presentation.
    data_viewmodel = DataViewModel(service=data_service)
    # Create the Dash app by injecting the view‑model.  The view
    # encapsulates all layout and callback definitions.
    dash_app = create_app(data_viewmodel)
    logger.info("Starting Dash server on %s:%s (debug=%s)...", config.HOST, config.PORT, config.DEBUG_MODE)
    # Use configuration values for host, port and debug mode.  This
    # allows these settings to be overridden via environment variables.
    dash_app.run_server(host=config.HOST, port=config.PORT, debug=config.DEBUG_MODE)


if __name__ == "__main__":
    main()