import pandas as pd
import re


class BaseUpdates:
    def __init__(self, driver):
        self.driver = driver
        self._scrape_updates()

    def _scrape_updates(self):
        updates = []
        for label, url in self.urls.items():
            updates_tags = self._find_updates(url)
            for u in updates_tags:
                updates.append(self._process_update_tag(u, label, url))
        self.updates = pd.DataFrame(updates)

    def _process_update_tag(self, update_tag, label, url):
        return {
            'municipality': self.municipality,
            'institution': self.institution,
            'label': label,
            'title': self._title_from_raw_html(update_tag),
            'date': self._date_from_raw_html(update_tag),
            'content': self._content_from_raw_html(update_tag),
            'url': url
        }

    def _title_from_raw_html(self, update_tag):
        raise NotImplementedError('This method should be overridden by a child class.')

    def _date_from_raw_html(self, update_tag):
        raise NotImplementedError('This method should be overridden by a child class.')

    def _content_from_raw_html(self, update_tag):
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
