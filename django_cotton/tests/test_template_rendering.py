from django_cotton.tests.utils import CottonTestCase
from django_cotton.tests.utils import get_compiled


class TemplateRenderingTests(CottonTestCase):
    def test_component_is_rendered(self):
        self.create_template(
            "cotton/render.html",
            """<div class="i-am-component">{{ slot }}</div>""",
        )

        self.create_template(
            "view.html",
            """<c-render>Hello, World!</c-render>""",
            "view/",
        )

        # Override URLconf
        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            self.assertContains(response, '<div class="i-am-component">')
            self.assertContains(response, "Hello, World!")

    def test_nested_rendering(self):
        self.create_template(
            "cotton/parent.html",
            """
                <div class="i-am-parent">
                    {{ slot }}
                </div>            
            """,
        )

        self.create_template(
            "cotton/child.html",
            """
                <div class="i-am-child"></div>
            """,
        )

        self.create_template(
            "cotton/nested_render_view.html",
            """
            <c-parent>
                <c-child>d</c-child>
            </c-parent>            
            """,
            "view/",
        )

        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            self.assertContains(response, '<div class="i-am-parent">')
            self.assertContains(response, '<div class="i-am-child">')

    def test_self_closing_is_rendered(self):
        self.create_template("cotton/self_closing.html", """I self closed!""")
        self.create_template(
            "self_closing_view.html",
            """
                1: <c-self-closing/>
                2: <c-self-closing />
                3: <c-self-closing  />
            """,
            "view/",
        )

        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            self.assertContains(response, "1: I self closed!")
            self.assertContains(response, "2: I self closed!")
            self.assertContains(response, "3: I self closed!")

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
        self.create_template(
            "cotton/spaces.html",
            """
                <c-vars var1="Hello" var2="World" />
                <div>{{ var1 }} {{ var2 }}</div>
            """,
        )
        self.create_template(
            "spaces_view.html",
            """
                <c-spaces var1="Hello" var2="World" />
            """,
            "view/",
        )

        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            self.assertContains(response, "<div>Hello World</div>")

    def test_encoding_is_retained_through_compilation(self):
        many_encoded_html_chars = "".join(
            [
                "&lt;",
                "&gt;",
                "&amp;",
                "&quot;",
                "&#39;",
                "&#x27;",
                "&#x2F;",
                "&#x60;",
            ]
        )
        compiled = get_compiled(many_encoded_html_chars)
        self.assertTrue(many_encoded_html_chars in compiled)

    def test_querystring_can_be_rendered(self):
        self.create_template("cotton/querystring.html", """{% querystring %}""")
        self.create_template(
            "querystring_view.html",
            """
                <c-querystring />
            """,
            "view/",
        )

        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/", data={"foo": "bar"})
            self.assertContains(response, "?foo=bar")

    def test_cvars_isnt_changing_global_context(self):
        self.create_template(
            "cotton/cvars_child.html",
            """
            <c-vars />
            
            name: child (class: {{ class }})
            """,
        )
        self.create_template(
            "cotton/cvars_parent.html",
            """
            name: parent (class: {{ class }}))
            
            {{ slot }}
            """,
        )

        self.create_template(
            "slot_scope_view.html",
            """
            <c-cvars-parent>
                <c-cvars-child class="testy" />
            </c-cvars-parent>
            """,
            "view/",
        )

        # Override URLconf
        with self.settings(ROOT_URLCONF=self.url_conf()):
            response = self.client.get("/view/")
            self.assertTrue("name: child (class: testy)" in response.content.decode())
            self.assertTrue("name: parent (class: )" in response.content.decode())
