from HTMLParser import HTMLParser
import markdown

class Stripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, data):
        self.fed.append(data)
    def get_data(self):
        return ''.join(self.fed)


def strip_html(html):
    stripper = Stripper()
    stripper.feed(html)
    return stripper.get_data()

def attach_summary(entries):
    for entry in entries:
        entry["html"] = strip_html(markdown.markdown(entry["markdown"]))
        if len(entry["html"]) > 300:
            entry["html"] = entry["html"][:300]
    return

