from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import re


class BaseUpdates:
    def __init__(self, driver):
        self.driver = driver
        self.bg_month_map = {
            'януари': '01',
            'февруари': '02',
            'март': '03',
            'април': '04',
            'май': '05',
            'юни': '06',
            'юли': '07',
            'август': '08',
            'септември': '09',
            'октомври': '10',
            'ноември': '11',
            'декември': '12'
        }
        self._scrape_updates()

    def _scrape_updates(self):
        updates = []
        for label, url in self.urls.items():
            updates_tags = self._find_updates(url)
            for u in updates_tags:
                updates.append(self._process_update_tag(u, label, url))
        self.updates = pd.DataFrame(updates)

    def _process_update_tag(self, update_tag, label, url):
        update_url = self._url_from_raw_html(update_tag)
        if not update_url:
            update_url = url

        return {
            'municipality': self.municipality,
            'institution': self.institution,
            'label': label,
            'title': self._title_from_raw_html(update_tag),
            'date': self._date_from_raw_html(update_tag),
            'content': self._content_from_raw_html(update_tag),
            'url': update_url
        }

    def wait_staleness(self, element):
        def not_staleness_of(element):
            '''The opposite of:
            https://www.selenium.dev/selenium/docs/api/py/_modules/selenium/webdriver/support/expected_conditions.html#staleness_of
            '''
            def _predicate(_):
                try:
                    # Calling any method forces a staleness check
                    element.is_enabled()
                    return True
                except StaleElementReferenceException:
                    return False

            return _predicate

        wait = WebDriverWait(self.driver, 20)
        wait.until(not_staleness_of(element))

    def _title_from_raw_html(self, update_tag):
        raise NotImplementedError('This method should be overridden by a child class.')

    def _date_from_raw_html(self, update_tag):
        raise NotImplementedError('This method should be overridden by a child class.')

    def _content_from_raw_html(self, update_tag):
        raise NotImplementedError('This method should be overridden by a child class.')

    def _url_from_raw_html(self, update_tag):
        raise NotImplementedError('This method should be overridden by a child class.')


class PernikVikUpdates(BaseUpdates):
    def __init__(self, driver):
        self.municipality = 'Перник'
        self.institution = 'ВиК'
        self.urls = {
            'Новини': 'http://www.vik-pernik.eu/single.php?name=%CD%EE%E2%E8%ED%E8',
            'Ремонтни дейности': 'http://www.vik-pernik.eu/single.php?name=%D0%E5%EC%EE%ED%F2%ED%E8%20%E4%E5%E9%ED%EE%F1%F2%E8'
        }
        super().__init__(driver)

    def _find_updates(self, url):
        self.driver.get(url)
        updates_tags = (
            self.driver
            .find_element_by_class_name('about_post')
            .find_element_by_tag_name('table')
            .find_elements_by_tag_name('tr')
        )

        for u in updates_tags:
            update_tag = u.find_element_by_tag_name('td')
            try:
                yield (
                    update_tag
                    .find_element_by_tag_name('div')
                    .find_element_by_tag_name('div')
                )
            except:
                # the tag doesn't contain an actual update, so we skip it
                continue

    def _title_from_raw_html(self, update_tag):
        try:
            # check if there is any bold text that we can treat as a title for the update
            title = (
                update_tag
                .find_element_by_tag_name('b')
                .text
            )
            assert title, 'The title does not contain any characters.'
            return title
        except:
            try:
                # check if there is any bold text that we can treat as a title for the update
                title = (
                    update_tag
                    .find_element_by_tag_name('div')
                    .find_element_by_tag_name('b')
                    .text
                )
                assert title, 'The title does not contain any characters.'
                return title
            except:
                # if there is no bold text, just treat the beginning of the text as the title
                return update_tag.text[: 50]

    def _date_from_raw_html(self, update_tag):
        date_string = (
            update_tag
            .find_element_by_tag_name('div')
            # get the second div, which contains the published date
            .find_elements_by_tag_name('div')[1]
            .text
        )
        date_match = re.search(
            r'\d{2}.\d{2}.\d{4}, \d{2}:\d{2}:\d{2}',
            date_string
        )
        
        if date_match:
            date_string = date_match[0]
            # convert the date string to ISO
            date_string = (
                date_string[6: 10]
                + '-'
                + date_string[3: 5]
                + '-'
                + date_string[0: 2]
                + ' '
                + date_string[12: ]
            )
            return pd.Timestamp(date_string)
        else:
            date_match = re.search(
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
                date_string
            )
            if date_match:
                return pd.Timestamp(date_match[0])
            else:
                raise ValueError('No date can be found in the update tag.')

    def _content_from_raw_html(self, update_tag):
        return (
            update_tag
            .find_element_by_tag_name('div')
            .find_element_by_tag_name('div')
            .text
        )

    def _url_from_raw_html(self, update_tag):
        return None


class PernikToploUpdates(BaseUpdates):
    def __init__(self, driver):
        self.municipality = 'Перник'
        self.institution = 'Топлофикация'
        self.urls = {
            'Новини': 'https://toplo-pernik.com/news/'
        }
        super().__init__(driver)

    def _find_updates(self, url):
        self.driver.get(url)

        updates_tags = (
            self.driver
            .find_element_by_class_name('jet-smart-listing')
            .find_elements_by_class_name('jet-smart-listing__featured')
        )
        updates_tags += (
            self.driver
            .find_element_by_class_name('jet-smart-listing')
            .find_elements_by_class_name('jet-smart-listing__post')
        )
        return updates_tags

    def _title_from_raw_html(self, update_tag):
        try:
            title_tag = (
                update_tag
                .find_element_by_class_name('jet-smart-listing__post-title')
            )
            self.wait_staleness(title_tag)
            title = title_tag.text
            assert title, 'The title does not contain any characters.'
            return title
        except:
            return update_tag.text[: 50]

    def _date_from_raw_html(self, update_tag):
        date_tag = (
            update_tag
            .find_element_by_class_name('post__date')
        )
        self.wait_staleness(date_tag)
        date_string = date_tag.text

        date_match = re.search(
            r'\d{2}.\d{2}.\d{4}',
            date_string
        )

        if date_match:
            date_string = date_match[0]
            # convert the date string to ISO
            date_string = (
                date_string[6: 10]
                + '-'
                + date_string[3: 5]
                + '-'
                + date_string[0: 2]
            )
            return pd.Timestamp(date_string)
        else:
            raise ValueError('No date can be found in the update tag.')

    def _content_from_raw_html(self, update_tag):
        content_tag = (
            update_tag
            .find_element_by_class_name('jet-smart-listing__post-excerpt')
        )
        self.wait_staleness(content_tag)
        return content_tag.text

    def _url_from_raw_html(self, update_tag):
        url_tag = (
            update_tag
            .find_element_by_class_name('jet-smart-listing__more')
        )
        self.wait_staleness(url_tag)
        return url_tag.get_attribute('href')


class PernikElektroUpdates(BaseUpdates):
    def __init__(self, driver):
        self.municipality = 'Перник'
        self.institution = 'Електрозахранване'
        self.urls = {
            'Новини': 'https://electrohold.bg/bg/mediya-centr-group/novini/'
        }
        super().__init__(driver)

    def _find_updates(self, url):
        self.driver.get(url)
        updates_tags = (
            self.driver
            .find_element_by_class_name('news-card')
            .find_elements_by_class_name('card-wrapper')
        )
        for u in updates_tags:
            self.wait_staleness(u)
            if 'перник' in u.text.lower():
                # return only updates that are relevant for Pernik
                yield update_tag

    def _title_from_raw_html(self, update_tag):
        try:
            title = (
                update_tag
                .find_element_by_class_name('card-content__title')
                .text
            )
            assert title, 'The title does not contain any characters.'
            return title
        except:
            return update_tag.text[: 50]

    def _date_from_raw_html(self, update_tag):
        date_string = (
            update_tag
            .find_element_by_class_name('card-content__data')
            .text
        )

        date_match = re.search(
            r'\d{2} [а-я]{3,} \d{4}',
            date_string
        )

        if date_match:
            date_string = date_match[0]
            # convert the date string to ISO
            date_string = (
                date_string[-4: ]
                + '-'
                + self.bg_month_map[date_string[3: -5]]
                + '-'
                + date_string[0: 2]
            )
            return pd.Timestamp(date_string)
        else:
            raise ValueError('No date can be found in the update tag.')

    def _content_from_raw_html(self, update_tag):
        return (
            update_tag
            .find_element_by_class_name('card-content__text')
            .text
        )

    def _url_from_raw_html(self, update_tag):
        return (
            update_tag
            .find_element_by_class_name('card-content__button')
            .get_attribute('href')
        )
