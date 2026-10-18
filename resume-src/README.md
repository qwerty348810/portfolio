# Исходники резюме

`resume.json` — общий источник фактов для PDF на сайте и версии для hh.ru.

Для сборки нужен Python с ReportLab и шрифт Arial (Windows) либо DejaVu Sans (Linux):

```text
python resume-src/build_resume.py
```

Результат: `resume.pdf` в корне сайта; PDF, TXT по разделам и редактируемый DOCX для hh.ru в `.cache/resume-hh/`.

Даты, образование и контакты перенесены из предыдущего PDF. Собственные проекты отделены от опыта работы; задача с иконкой iOS относится к Foodpicasso. Ссылки на приватные репозитории не включаются.
