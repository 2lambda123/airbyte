import logging

import requests

from .base_extract import BaseExtract


class HttpResourceExtract(BaseExtract):
    def __init__(self, **kwargs):
        super(HttpResourceExtract, self).__init__(**kwargs)

        self.request = self._build_step('request', **kwargs)
        self.decoder = self._build_step('decoder', **kwargs)
        self.selector = self._build_step('selector', **kwargs)
        self.pagination = self._build_step('pagination', **kwargs)
        self.state = self._build_step('state', **kwargs)
        self.request = self._build_step('request', **kwargs)

    def extract(self, context):
        context = {
            'config': context.get('config'),
            'state': context.get('state'),
            'var': context.get('var'),
        }

        state = None

        for page in self.pagination.iterate(context):
            context['page'] = page

            context['request'] = self.request.build(context)
            context['response'] = requests.request(**context['request'])
            context['decoded_response'] = self.decoder.decode(context)

            for record in self.selector.select(context):
                logging.debug(record)
                state = self.state.get(context)


            logging.debug(state)

    def _build_step(self, name, **kwargs):
        config = self.options[name]
        return self.strategy_builder(config['strategy'], config.get('options', {}), **kwargs)
