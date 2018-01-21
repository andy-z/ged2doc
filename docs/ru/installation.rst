.. highlight:: shell

=========
Установка
=========


Python - стабильный релиз
-------------------------

Для установки ged2doc как пакета в существующей установе Python (или в
виртуальной среде) используя текущую версию из PyPI достаточно запустить
комманду:

.. code-block:: console

    $ pip install ged2doc

Это самый предпочтительный метод установки, так как он всегда устанавливает
самый последний стабильный релиз и все необходимые зависимости.

Если в Вашей версии Python нет поддержки `pip`_, то используйте документацию
`Python installation guide`_ для установки ``pip``.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Python - установка из исходников
--------------------------------

Исходники ged2doc могут быть загружены из `Github`_.

Можно клонировать репозиторий:

.. code-block:: console

    $ git clone git://github.com/andy-z/ged2doc

Или загрузить `архив`_:

.. code-block:: console

    $ curl  -OL https://github.com/andy-z/ged2doc/tarball/master

Для установки исполните эту комманду в папке с исходниками:

.. code-block:: console

    $ python setup.py install


.. _Github: https://github.com/andy-z/ged2doc
.. _архив: https://github.com/andy-z/ged2doc/tarball/master


Вариант установки на Windows
----------------------------

Оба предыдущих варианта можно использовать на Windows, предварительно установив
Python, подойдет любой из дистрибутивов. Альтернативный вариант установки
на Windows не требует предварительной установки Python, вместо этого Вы
можете установить ged2com как отдельное приложение Windows, которое включает все
необходимые компоненты. Скачайте установщик (EXE файл) из `последнего релиза`_
и запустите его на вашем компьютере. После установки в Меню Программ и на
Пабочем столе появится ярлык ged2doc, который запускает окно командной строки с
доступом к команде ``ged2doc``.

.. _`последнего релиза`: https://github.com/andy-z/ged2doc/releases/latest
