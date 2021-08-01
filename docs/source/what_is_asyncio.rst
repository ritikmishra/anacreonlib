More about ``async`` and ``asyncio``
===============================================================================

Suppose we are writing an Anacreon bot that manages 100 fleets at the same time.
Each "fleet manager" may sleep for many minutes, waiting for fleets to get to
their destinations before taking action. 

Naively, we might write code that looks something like this

.. code-block:: python

    import time
    
    def manage_fleet(fleet_id):
        while True:
            ... # do some stuff
            time.sleep(60) # wait for next watch
            ... # do some more stuff

    fleets_to_manage = [...]
    for fleet in fleets_to_manage:
        manage_fleet(fleet)


However, this will take a lot of time to complete. We are for our 
"fleet manager" to completely finish managing one fleet before moving on to the
next. The call to ``time.sleep`` stops our whole program. As a result, the
script as written above could take many hours!

Wouldn't it be great if we could run all of our fleet managers **concurrently**?

By using coroutines and executing them on the ``asyncio`` event loop, we can
run these concurrently!

.. code-block:: python

    import time
    import asyncio

    async def manage_fleet(fleet_id):
        while True:
            ... # do some stuff
            await asyncio.sleep(60)
            ... # do some more stuff

    async def main():
        fleets_to_manage = [...]
        fleet_manager_tasks = []
        
        # concurrently run each manager on the asyncio event loop
        for fleet in fleets_to_manage:
            fleet_manager_tasks.append(asyncio.create_task(manage_fleet(fleet)))

        # wait for the managers to finish
        for manager in fleet_manager_tasks:
            await manager

    asyncio.run(main())


At a high level, a `coroutine` is a piece of computation that can be 
suspended/resumed. When we call ``manage_fleet``, it returns a ``coroutine``
object.

    >>> manage_fleet(10)
    <coroutine object manage_fleet at 0x7fd7c3b3e8c0>

In Python, we can resume these coroutines using their ``send`` method

    >>> async def foo():
    ...     print("Hello! I am a coroutine!")
    ...
    >>> coro = foo()
    >>> coro.send(None)
    Hello! I am a coroutine
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    StopIteration

Because Python coroutines are implemented using generators, when they are done,
they raise ``StopIteration``, similarly to how generators raise 
``StopIteration`` when they are complete. Coroutines can suspend at ``await``
points, yielding control back to the caller [#yieldcoro]_.

This is where :py:mod:`asyncio` comes in -- it provides an `event loop` [#talk]_
that manages our coroutines, is able to run them concurrently 
(using :py:func:`asyncio.create_task`), and resumes them when they are ready to
be resumed.

This is why :py:mod:`anacreonlib` is written with async -- to let users easily
write concurrent scripts. 

.. [#yieldcoro] The technical details about this are more complicated than 
    "coroutines suspend at ``await`` points". This 
    `answer on StackOverflow <https://stackoverflow.com/questions/59586879/does-await-in-python-yield-to-the-event-loop/59780868#59780868>`_  
    goes in depth about when exactly coroutines yield control back to the event
    loop.

.. [#talk] If you are interested in how you might go about writing an event 
    loop, check out `this talk <https://www.youtube.com/watch?v=Y4Gt3Xjd7G8>`_
    by David Beazley that goes over it.