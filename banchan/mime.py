def guess_mime_type(content, deftype):
    """Description: Guess the mime type of a block of text
    :param content: content we're finding the type of
    :type str:

    :param deftype: Default mime type
    :type str:

    :rtype: <type>:
    :return: <description>
    """
    # Mappings recognized by cloudinit
    starts_with_mappings = {
        '#include': 'text/x-include-url',
        '#!': 'text/x-shellscript',
        '#cloud-config': 'text/cloud-config',
        '#upstart-job': 'text/upstart-job',
        '#part-handler': 'text/part-handler',
        '#cloud-boothook': 'text/cloud-boothook'
    }
    rtype = deftype
    for possible_type, mimetype in starts_with_mappings.items():
        if content.startswith(possible_type):
            rtype = mimetype
            break
    return(rtype)
