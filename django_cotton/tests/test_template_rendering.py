from django_cotton.tests.utils import CottonTestCase
from django_cotton.tests.utils import get_compiled


class TemplateRenderingTests(CottonTestCase):
    def test_new_lines_in_attributes_are_preserved(self):
        self.create_template(
            "cotton/preserved.html",
            """<div {{ attrs }}>{{ slot }}</div>""",
        )

        self.create_template(
            "preserved_view.html",
            """
            <c-preserved x-data="{
                attr1: 'im an attr',
                var1: 'im a var',
                method() {
                    return 'im a method';
                }
            }" />
            """,
            "view/",
        )

        # Override URLconf
        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")

            self.assertTrue(
                """{
                attr1: 'im an attr',
                var1: 'im a var',
                method() {
                    return 'im a method';
                }
            }"""
                in response.content.decode()
            )

    def test_attributes_that_end_or_start_with_quotes_are_preserved(self):
        self.create_template(
            "cotton/preserve_quotes.html",
            """
        <div {{ attrs }}><div>
        """,
        )

        self.create_template(
            "preserve_quotes_view.html",
            """
            <c-preserve-quotes something="var ? 'this' : 'that'" />
            """,
            "view/",
        )

        # Override URLconf
        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")

            self.assertContains(response, '''"var ? 'this' : 'that'"''')

    def test_expression_tags_close_to_tag_elements_doesnt_corrupt_the_tag(self):
        html = """
            <div{% if 1 = 1 %} attr1="variable" {% endif %}></div>
        """

        rendered = get_compiled(html)

        self.assertFalse("</div{% if 1 = 1 %}>" in rendered, "Tag corrupted")
        self.assertTrue("</div>" in rendered, "</div> not found in rendered string")

    def test_conditionals_evaluation_inside_tags(self):
        self.create_template("cotton/conditionals_in_tags.html", """<div>{{ slot }}</div>""")
        self.create_template(
            "conditionals_in_tags_view.html",
            """
                <c-conditionals-in-tags>
                    <select>
                        <option value="1" {% if my_obj.selection == 1 %}selected{% endif %}>Value 1</option>
                        <option value="2" {% if my_obj.selection == 2 %}selected{% endif %}>Value 2</option>
                    </select>                         
                </c-conditionals-in-tags>
            """,
            "view/",
            context={"my_obj": {"selection": 1}},
        )
        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            self.assertContains(response, '<option value="1" selected>Value 1</option>')
            self.assertNotContains(response, '<option value="2" selected>Value 2</option>')

    def test_spaces_preserved_between_variables(self):
        self.create_template("cotton/spaces.html", """<div>{{ slot }}</div>""")
        self.create_template(
            "spaces_view.html",
            """
                <c-vars var1="Hello" var2="World" />
                <c-spaces var1="Hello" var2="World">{{ var1 }} {{ var2 }}</c-spaces>
            """,
            "view/",
        )

        # compiled = get_compiled(
        #     """
        #         <c-vars var1="Hello" var2="World" />
        #         <c-spaces var1="Hello" var2="World">{{ var1 }} {{ var2 }}</c-spaces>
        #     """
        # )
        # print(compiled)

        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            print(response.content.decode())
            self.assertContains(response, "<div>Hello World</div>")
