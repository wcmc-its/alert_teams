import sys
import json
import urllib.request, urllib.error, urllib.parse
import csv
import gzip
from collections import OrderedDict

def escape_markdown(text):
    # insert backslashes before symbols that are particular to markdown
    # asterisks
    text=str(text)
    text = text.replace("*", "\*")
    # octothorpes
    text = text.replace("#", "\#")
    # tilde
    text = text.replace("~", "\~")
    # underscores
    text = text.replace("_", "\_")
    return text


def send_webhook_request(url, body, user_agent=None):
    if url is None:
        print("ERROR No URL provided", file=sys.stderr)
        return False
    
    encoded_body = urllib.parse.urlencode(body).encode()
    print("INFO Sending POST request to url=%s with size=%d bytes payload" % (url, len(encoded_body)), file=sys.stderr)
    print("INFO Body: %s" % body, file=sys.stderr)
    try:
        req = urllib.request.Request(url, data=encoded_body, headers={"Content-Type": "application/json", "User-Agent": user_agent})
        res = urllib.request.urlopen(req)
        if 200 <= res.code < 300:
            print("INFO Webhook receiver responded with HTTP status=%d" % res.code, file=sys.stderr)
            return True
        else:
            print("ERROR Webhook receiver responded with HTTP status=%d" % res.code, file=sys.stderr)
            return False
    except urllib.error.HTTPError as e:
        print("ERROR Error sending webhook request: %s" % e, file=sys.stderr)
    except urllib.error.URLError as e:
        print("ERROR Error sending webhook request: %s" % e, file=sys.stderr)
    except ValueError as e:
        print("ERROR Invalid URL: %s" % e, file=sys.stderr)
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "--execute":
        print("FATAL Unsupported execution mode (expected --execute flag)", file=sys.stderr)
        sys.exit(1)
    try:
        raw_settings = sys.stdin.read()
        settings = json.loads(raw_settings, object_pairs_hook=OrderedDict)
        print("INFO Settings: %s" % raw_settings, file=sys.stderr)
        url = settings['configuration'].get('url')
        message = settings['configuration'].get('message')

        # build the list of facts from the search results
        facts = []
        for key,value in list(settings.get('result').items()):
            # teams uses markdown in the value field but not the name field
            value = escape_markdown(value)
            facts.append({"name":key, "value":value})

        # main message section
        section = {
            "activityTitle": "Splunk",
            "activitySubtitle": settings.get("search_name"),
            "text": message
        }
        # only set facts in the message if requested
        if settings['configuration'].get("send_facts") == "1":
            section["facts"] = facts

        # message card body
        body = {
            "@type":"MessageCard",
            "@context":"https://schema.org/extensions",
            "title":settings.get('search_name'),
            "summary":settings.get('search_name'),
            "sections":[
                section
            ],
            "potentialAction":[
                {
                "@context":"http://schema.org",
                "@type":"ViewAction",
                "name":"View in Splunk",
                "target":[settings.get('results_link')]
                }
            ]
        }
        user_agent = settings['configuration'].get('user_agent', 'Splunk')
        if not send_webhook_request(url, json.dumps(body), user_agent=user_agent):
            sys.exit(2)
    except Exception as e:
        print("ERROR Unexpected error: %s" % e, file=sys.stderr)
        sys.exit(3)
