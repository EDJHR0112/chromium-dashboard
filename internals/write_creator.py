import logging

from framework.basehandlers import FlaskHandler
from internals.models import Feature


class UpdateCreatorHandler(FlaskHandler):

  def get_template_data():
    """Writes string creator field from created_by user field."""
    q = Feature.query()
    features = q.fetch()
    update_count = 0
    for feature in features:
      if feature.created_by and not feature.creator:
        update_count += 1
        email = "Unknown"
        if feature.created_by:
            email = feature.created_by.email()
        feature.creator = email
        feature.put(notify=False)
    
    logging.info(f'{update_count} features updated with new creator field.')
    return 'Success'
