#!/usr/bin/env python3

import multiprocessing as mp
import os
import re
import sys
from multiprocessing import Manager
from multiprocessing import Pool as ThreadPool
from pathlib import Path
from urllib.parse import urlparse

import requests
import tld
import tldextract
import tqdm
from create_filter_rules import create_filterlist_rules

sys.path.insert(1,  "/home/c6/Documents/Brave/pagegraph-tracking/analysis")
import logging

import utilities


def url_polisher(url, root_url):

    url = url.strip()
    root_url = root_url.strip()
    
    if url == '':
        return url
    
    # if url starts with /
    if re.match(r'^/\w+', str(url)):
        if root_url.endswith('/'):
            url = root_url[:-1] + url
        else:
            url = root_url + url

    # if url starts with //
    if re.match(r'^//\w+', str(url)):
        url = "https:" + url
        # if root_url.endswith('/'):
        #     url = root_url[:-1] + url
        # else:
        #     url = root_url + url
    
    if not url.startswith('http'):
        url = "https://" + url

    return url

def is_ulr_valid(url):
    if url == '':
        return False
    # logging_file = Path.home().joinpath(Path.cwd(), "filterlists/url_validation.log")
    # logging.basicConfig(filename=logging_file, level=logging.ERROR)
    try:
        tld.get_fld(url)
        return True

    except Exception as e:
        # print("URL validating", url, e)
        # logging.error(str(e)+ " : "+ url + " : " + root_url)
        return False

def get_domain(url):
    """
    Return the top level domains
    Args:
        url: a single/list of urls
    """
    try:
        u = tldextract.extract(url)
        return "https://" + u.domain + "." + u.suffix
    except Exception as e:
        print(e)
        return ''


def get_resource_type(url):
    """
    Function to get resource type of a node.
    Args:
        url
    Returns:
        Resource type of node.
    """
    try:
        response = requests.head(url, timeout=5,  headers={"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"},)
        content_type = response.headers['content-type'].split(';')[0]
        if content_type.count(';') >=1:
            content_type.split(';')[0]
    except Exception as e:
        content_type = "unknown"
        print(url)
        print(e)

    javascript_mimetype = ["text/javascript", "application/javascript", "application/ecmascript",
                           "application/x-ecmascript", "application/x-javascript", "text/ecmascript",
                           "text/javascript1.0", "text/javascript1.1", "text/javascript1.2", "text/javascript1.3",
                           "text/javascript1.4",
                           "text/javascript1.5", "text/livescript", "text/x-ecmascript", "text/x-javascript"]
    image_memetype = ["image/apng", "image/avif", "image/gif", "image/jpeg", "image/png", "image/svg+xml", "image/webp",
                      "image/vnd.microsoft.icon"]

    # script
    match = [script for script in javascript_mimetype if script == content_type]
    if len(match) == 1:
        return "script"
    # image
    match = [image for image in image_memetype if image == content_type]
    if len(match) == 1:
        return "image"
    # stylesheet
    if content_type == "text/html":
        return "stylesheet"
    else:
        return None


def match_url(top_level_url, root_url, current_url, resource_type, rules_dict):
    """
    Function to match node information with filter list rules.
    Args:
        domain_top_level: eTLD+1 of visited page. => root_url
        current_domain; Domain of request being labelled.
        current_url: URL of request being labelled.
        resource_type: Type of request being labelled (from content policy type).
        rules_dict: Dictionary of filter list rules.
    Returns:
        Label indicating whether the rule should block the node (True/False).
    """

    try:
        if top_level_url == get_domain(root_url):
            third_party_check = False
        else:
            third_party_check = True

        if resource_type == 'sub_frame':
            subdocument_check = True
        else:
            subdocument_check = False

        if resource_type == 'script':
            if third_party_check:
                rules = rules_dict['script_third']
                options = {'third-party': True, 'script': True,
                           'domain': top_level_url, 'subdocument': subdocument_check}
            else:
                rules = rules_dict['script']
                options = {'script': True, 'domain': top_level_url,
                           'subdocument': subdocument_check}

        elif resource_type == 'image' or resource_type == 'imageset':
            if third_party_check:
                rules = rules_dict['image_third']
                options = {'third-party': True, 'image': True,
                           'domain': top_level_url, 'subdocument': subdocument_check}
            else:
                rules = rules_dict['image']
                options = {'image': True, 'domain': top_level_url,
                           'subdocument': subdocument_check}

        elif resource_type == 'stylesheet':
            if third_party_check:
                rules = rules_dict['css_third']
                options = {'third-party': True, 'stylesheet': True,
                           'domain': top_level_url, 'subdocument': subdocument_check}
            else:
                rules = rules_dict['css']
                options = {'stylesheet': True, 'domain': top_level_url,
                           'subdocument': subdocument_check}

        elif resource_type == 'xmlhttprequest':
            if third_party_check:
                rules = rules_dict['xmlhttp_third']
                options = {'third-party': True, 'xmlhttprequest': True,
                           'domain': top_level_url, 'subdocument': subdocument_check}
            else:
                rules = rules_dict['xmlhttp']
                options = {'xmlhttprequest': True, 'domain': top_level_url,
                           'subdocument': subdocument_check}

        elif third_party_check:
            rules = rules_dict['third']
            options = {'third-party': True, 'domain': top_level_url,
                       'subdocument': subdocument_check}

        else:
            rules = rules_dict['domain']
            options = {'domain': top_level_url,
                       'subdocument': subdocument_check}

        return rules.should_block(current_url, options)

    except Exception as e:
        return False


def run_match_url(top_level_url, root_url, current_url, resource_type,
                  rules_dict, filterlists):
    for fl in filterlists:
        if match_url(top_level_url, root_url, current_url, resource_type, rules_dict[fl]):
            return True
    return False



def is_tracking(url, root_url, filterlists, filterlist_rules):
    
    """
    The initial point to start labeling
    Required arguments to pass to functions:
        url: the url we want to check its tracking status
        root_url: the domain included this url
        filterlists: List of filter list names.
        filterlist_rules: Dictionary of filter lists and their rules.
    """
    
    
    # check tracking status of the url
    url = url_polisher(url, root_url)
    if is_ulr_valid(url):
        if run_match_url(get_domain(url), root_url, url, "script", filterlist_rules,
                        filterlists):
            return True
    return False

if __name__ == "__main__":
    is_tracking()