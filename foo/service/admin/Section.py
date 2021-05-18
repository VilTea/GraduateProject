import foo.utils.SectionUtils as SectionUtils

section_dict = SectionUtils.get_section_list()


def refresh():
    global section_dict
    section_dict = SectionUtils.get_section_list()