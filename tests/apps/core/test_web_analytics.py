"""
Test suite for the Web Analytics
"""
from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory
from django.test.utils import override_settings

from cms.test_utils.testcases import CMSTestCase
from parler.models import TranslationDoesNotExist

from richie.apps.core.context_processors import WebAnalyticsContextProcessor
from richie.apps.courses.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
)
from richie.apps.courses.models.course import CourseRun, CourseRunTranslation


class WebAnalyticsTestCase(CMSTestCase):
    """Testing the Web Analytics django app"""

    @override_settings(
        WEB_ANALYTICS_ID="UA-XXXXXXXXX-X",
        WEB_ANALYTICS_PROVIDER="google_analytics",
        WEB_ANALYTICS_LOCATION="head",
    )
    def test_web_analytics_organization_page(self):
        """
        Test Web Analytics with a organization page on js on html head
        """
        org_page_code = "PUBLIC_ORG"
        org_page_title = "public title"

        # Create an Organization
        organization = OrganizationFactory(
            page_title=org_page_title, should_publish=True, code=org_page_code
        )
        page = organization.extended_object
        url = page.get_absolute_url(language="en")
        response = self.client.get(url)

        self.assertContains(
            response,
            "google-analytics.com",
            msg_prefix="Page should include the Google Analytics js code",
        )
        self.assertContains(
            response,
            "UA-XXXXXXXXX-X",
            msg_prefix="Page should include the Google Analytics tracking id code",
        )
        self.assertRegex(
            response.content.decode("UTF-8"),
            "dimension1.*" + org_page_code,
            msg="Google Analytics should include organization code on the first custom dimension",
        )
        self.assertRegex(
            response.content.decode("UTF-8"),
            "dimension5.*" + org_page_title,
            msg="Google Analytics should include page title on the 5th custom dimension",
        )
        response_content = response.content.decode("UTF-8")
        self.assertGreater(
            response_content.index("<body"),
            response_content.index("google-analytics.com"),
            "Web tracking should be at the bottom of the page",
        )

    @override_settings(
        WEB_ANALYTICS_ID="UA-XXXXXXXXX-X",
        WEB_ANALYTICS_PROVIDER="google_analytics",
        WEB_ANALYTICS_LOCATION="footer",
    )
    def test_web_analytics_course_page(self):
        """
        Test Web Analytics with a course page with js at the bottom of the html page
        """
        org_page_code = "PUBLIC_ORG"
        org_page_title = "public title"

        # Create an Organization
        organization = OrganizationFactory(
            page_title=org_page_title, should_publish=True, code=org_page_code
        )

        course_page_code = "XPTO_CODE_FOR_COURSE"
        course_page_title = {
            "en": "A fancy title for a course",
            "fr": "Un titre fantaisiste pour un cours",
        }
        course = CourseFactory(
            page_title=course_page_title,
            fill_organizations=[organization],
            code=course_page_code,
        )

        course_run_link = (
            "http://example.edx:8073/courses/course-v1:edX+DemoX+01/course/"
        )
        course_run_title = "Édition d'automne"
        course_run_title_safe = "Édition d&#x27;automne"
        CourseRunFactory(
            direct_course=course,
            resource_link=course_run_link,
            sync_mode="sync_to_public",
            title=course_run_title,
            languages=["en", "fr"],
        )

        course_page = course.extended_object
        # publish after course run creation so the course run is also published
        course_page.publish("fr")
        course_page.publish("en")

        url = course_page.get_absolute_url(language="fr")
        response = self.client.get(url)

        self.assertContains(
            response,
            "google-analytics.com",
            msg_prefix="Page should include the Google Analytics snippet code",
        )
        self.assertContains(
            response,
            "UA-XXXXXXXXX-X",
            msg_prefix="Page should include the Google Analytics tracking code",
        )
        response_content = response.content.decode("UTF-8")
        self.assertRegex(
            response_content,
            "dimension1.*" + org_page_code,
            msg="Should include organization code on the 1st custom dimension",
        )
        self.assertRegex(
            response_content,
            "dimension2.*" + course_page_code,
            msg="Should include course code on the 2nd custom dimension",
        )
        self.assertRegex(
            response_content,
            "dimension3.*" + course_run_title_safe,
            msg="Should include course run title on the 3rd custom dimension",
        )
        self.assertContains(
            response,
            "dimension4': '" + course_run_link,
            msg_prefix="Should include course resource link on the 4th custom dimension",
        )
        self.assertRegex(
            response_content,
            "dimension5.*" + course_page_title.get("fr"),
            msg="Should include course page title on the 5th custom dimension",
        )
        self.assertGreater(
            response_content.index("google-analytics.com"),
            response_content.index("<body"),
            "Web tracking should be at the bottom of the page",
        )

    @override_settings(
        WEB_ANALYTICS_ID="XXXXX-YYYYYY",
        WEB_ANALYTICS_PROVIDER="custom-web-analytics-provider",
    )
    def test_web_analytics_enabled_without_google_analytics(self):
        """
        Test Web Analytics with a organization page using a custom provider. Can test the html
        because the information is only on the template context.
        """
        org_page_code = "PUBLIC_ORG"
        org_page_title = "public title"

        # Create an Organization
        organization = OrganizationFactory(
            page_title=org_page_title, should_publish=True, code=org_page_code
        )

        course_page_code = "XPTO_CODE_FOR_COURSE"
        course_page_title = {
            "en": "A fancy title for a course",
            "fr": "Un titre fantaisiste pour un cours",
        }
        course = CourseFactory(
            page_title=course_page_title,
            fill_organizations=[organization],
            code=course_page_code,
        )

        course_page = course.extended_object
        # publish after course run creation so the course run is also published
        course_page.publish("fr")
        course_page.publish("en")

        url = course_page.get_absolute_url(language="fr")

        request = RequestFactory().get(url)
        request.current_page = course_page

        context = WebAnalyticsContextProcessor().context_processor(request)
        dimensions = context["WEB_ANALYTICS_DIMENSIONS"]
        self.assertListEqual(list(dimensions["organizations_codes"]), ["PUBLIC_ORG"])
        self.assertListEqual(dimensions["course_code"], ["XPTO_CODE_FOR_COURSE"])
        self.assertListEqual(dimensions["course_runs_titles"], [])
        self.assertListEqual(list(dimensions["course_runs_resource_links"]), [])
        self.assertListEqual(dimensions["page_title"], ["A fancy title for a course"])

    @override_settings(WEB_ANALYTICS_ID="YYY-ZZZ-WWW")
    def test_web_analytics_with_only_id(self):
        """
        Test Web Analytics with only the web analytics id setting. Test the default values of
        provider and location.
        """
        course = CourseFactory()
        page = course.extended_object
        page.publish(settings.LANGUAGE_CODE)
        url = page.get_absolute_url(language=settings.LANGUAGE_CODE)
        response = self.client.get(url)
        response_content = response.content.decode("UTF-8")

        self.assertContains(
            response,
            "google-analytics.com",
            msg_prefix="Page should include the Google Analytics snippet code",
        )
        self.assertGreater(
            response_content.index("<body"),
            response_content.index("google-analytics.com"),
            "Web tracking should be at the head of the page",
        )
        self.assertContains(
            response,
            "YYY-ZZZ-WWW",
            msg_prefix="Page should include the Web Analytics id",
        )

    @override_settings(
        WEB_ANALYTICS_ID="UA-XXXXXXXXX-X", WEB_ANALYTICS_PROVIDER="google_analytics"
    )
    def test_web_analytics_course_page_course_run_without_title(self):
        """
        Test Web Analytics with a course page that has a course run without a title translation
        """
        course = CourseFactory()

        course_run = CourseRun(
            direct_course=course,
            languages=["fr"],
            title=None,
        )
        course_run.save()

        CourseRunTranslation.objects.all().delete()
        course_run.refresh_from_db()

        self.assertFalse(CourseRunTranslation.objects.exists())
        self.assertEqual(course_run.title, None)

        cache.clear()

        # reread course run from database
        course_run = CourseRun.objects.first()

        self.assertIsNone(
            course_run.safe_title,
            msg="Course run without a title should return None on safe_title property",
        )

        with self.assertRaises(
            TranslationDoesNotExist,
            msg="Verify that the 'title' method unfortunately is raising an error",
        ):
            course_run.title  # pylint: disable=pointless-statement

        page = course.extended_object
        page.publish(settings.LANGUAGE_CODE)
        url = page.get_absolute_url(language=settings.LANGUAGE_CODE)
        response = self.client.get(url)

        self.assertContains(
            response,
            "dimension3': ''",
            msg_prefix="Should include an empty course run title on the 3rd custom dimension",
        )

    @override_settings(
        WEB_ANALYTICS_ID="UA-XXXXXXXXX-X", WEB_ANALYTICS_PROVIDER="google_tag_manager"
    )
    def test_web_analytics_google_tag_manager(self):
        """
        Test Google Tag Manager has Web Analytics provider for a course page with all the
        dimensions.
        """
        org_page_code = "PUBLIC_ORG"
        org_page_title = "public title"

        # Create an Organization
        organization = OrganizationFactory(
            page_title=org_page_title, should_publish=True, code=org_page_code
        )

        course_page_code = "XPTO_CODE_FOR_COURSE"
        course_page_title = {
            "en": "A fancy title for a course",
            "fr": "Un titre fantaisiste pour un cours",
        }
        course = CourseFactory(
            page_title=course_page_title,
            fill_organizations=[organization],
            code=course_page_code,
        )

        course_run_link = (
            "http://example.edx:8073/courses/course-v1:edX+DemoX+01/course/"
        )
        course_run_title = "Édition d'automne"
        course_run_title_safe = "Édition d&#x27;automne"
        CourseRunFactory(
            direct_course=course,
            resource_link=course_run_link,
            sync_mode="sync_to_public",
            title=course_run_title,
            languages=["en", "fr"],
        )

        course_page = course.extended_object
        # publish after course run creation so the course run is also published
        course_page.publish("fr")
        course_page.publish("en")

        url = course_page.get_absolute_url(language="fr")
        response = self.client.get(url)

        self.assertContains(
            response,
            "googletagmanager.com",
            msg_prefix="Page should include the Google Tag Manager js code",
        )
        self.assertContains(
            response,
            "UA-XXXXXXXXX-X",
            msg_prefix="Page should include the Google Tag Manager tracking id code",
        )
        response_content = response.content.decode("UTF-8")
        self.assertRegex(
            response_content,
            "dimension1.*" + org_page_code,
            msg="Should include organization code on the 1st custom dimension",
        )
        self.assertRegex(
            response_content,
            "dimension2.*" + course_page_code,
            msg="Should include course code on the 2nd custom dimension",
        )
        self.assertRegex(
            response_content,
            "dimension3.*" + course_run_title_safe,
            msg="Should include course run title on the 3rd custom dimension",
        )
        self.assertContains(
            response,
            "dimension4': '" + course_run_link,
            msg_prefix="Should include course resource link on the 4th custom dimension",
        )
        self.assertRegex(
            response_content,
            "dimension5.*" + course_page_title.get("fr"),
            msg="Should include course page title on the 5th custom dimension",
        )
