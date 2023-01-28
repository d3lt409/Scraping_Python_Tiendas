import logging
from scrapy.exceptions import NotConfigured
from scrapy import signals
logger = logging.getLogger(__name__)

class CustomLogExtension:

    def __init__(self):
        self.level = logging.WARNING
        self.modules = ['scrapy.utils.log', 'scrapy.middleware',
                        'scrapy.extensions.logstats', 'scrapy.statscollectors', 
                        'scrapy.core.engine', 'scrapy.core.scraper', 
                        'scrapy.crawler', 'scrapy.extensions', 
                        __name__]
        for module in self.modules:
            logger = logging.getLogger(module)
            logger.setLevel(self.level)

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('CUSTOM_LOG_EXTENSION'):
            raise NotConfigured
        ext = cls()
        crawler.signals.connect(
            ext.spider_opened, signal=signals.spider_opened
        )
        return ext

    def spider_opened(self, spider):
        logger.debug("This log should not appear.")