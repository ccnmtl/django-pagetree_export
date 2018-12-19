from __future__ import unicode_literals, print_function

from pagetree_export import register_class as register
import quizblock.models as quizblock
from pagetree_export.utils import asbool, sanitize


@register
class Quiz(object):
    block_class = quizblock.Quiz
    identifier = 'quiz'

    def exporter(self, block, xmlfile, zipfile):
        filename = "pageblocks/%s-description.txt" % block.pageblock().pk
        zipfile.writestr(filename, block.description.encode("utf8"))

        print('<quiz rhetorical="%s" description_src="%s">' % (
            block.rhetorical, filename),
              file=xmlfile)

        for question in block.question_set.all():
            print('<question type="%s">' % (
                question.question_type),
                  file=xmlfile)

            filename = "pageblocks/%s-%s-text.txt" % (
                block.pageblock().pk, question.pk)
            zipfile.writestr(filename, question.text.encode("utf8"))
            print("<text src='%s' />" % filename, file=xmlfile)

            filename = "pageblocks/%s-%s-explanation.txt" % (
                block.pageblock().pk, question.pk)
            zipfile.writestr(filename, question.explanation.encode("utf8"))
            print("<explanation src='%s' />" % filename, file=xmlfile)

            filename = "pageblocks/%s-%s-introtext.txt" % (
                block.pageblock().pk, question.pk)
            zipfile.writestr(filename, question.intro_text.encode("utf8"))
            print("<introtext src='%s' />" % filename, file=xmlfile)

            for answer in question.answer_set.all():
                print(
                    '<answer label="%s" value="%s" correct="%s" />' % (
                        sanitize(answer.label), answer.value, answer.correct),
                    file=xmlfile)

            print("</question>", file=xmlfile)
        print("</quiz>", file=xmlfile)

    def importer(self, node, zipfile):
        children = node.getchildren()
        assert len(children) == 1 and children[0].tag == "quiz"
        rhetorical = asbool(children[0].get("rhetorical"))
        path = children[0].get("description_src")
        description = zipfile.read(path)
        q = quizblock.Quiz(rhetorical=rhetorical, description=description)
        q.save()

        for child in children[0].iterchildren():
            assert child.tag == "question"
            type = child.get("type")

            text, explanation, introtext, answers = \
                child.getchildren()[:3] + [child.getchildren()[3:]]
            path = text.get("src")
            text = zipfile.read(path)
            path = explanation.get("src")
            explanation = zipfile.read(path)
            path = introtext.get("src")
            introtext = zipfile.read(path)
            question = quizblock.Question(
                quiz=q, text=text, question_type=type,
                explanation=explanation,
                intro_text=introtext)
            question.save()

            for answer in answers:
                label = answer.get("label")
                value = answer.get("value")
                correct = asbool(answer.get("correct"))
                answer = quizblock.Answer(
                    question=question,
                    value=value, label=label, correct=correct)
                answer.save()

        return q
