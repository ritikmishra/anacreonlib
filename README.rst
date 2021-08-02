anacreonlib
===========

|PyPI Version| |Documentation Status|

This **unofficial** library provides a Python interface to the API of
`Anacreon 3 <https://anacreon.kronosaur.com>`_, which is an online 
`4X <https://en.wikipedia.org/wiki/4X>`_ game produced by
`Kronosaur Productions, LLC. <http://kronosaur.com/>`_.

The minimum supported Python version is 3.8

Make sure to read the "Scripts and Bots" section of the 
`Kronosaur Terms of Service <https://multiverse.kronosaur.com/news.hexm?id=97#:~:text=scripts%20and%20bots>`_.

Installation
=============

``anacreonlib`` can be installed using pip::

   $ pip install anacreonlib

Usage
=====

Below is a minimum working example to get started with using the Anacreon API

.. code-block:: python

    from anacreonlib import Anacreon, Fleet
    import asyncio

    async def main():
        ## Step 1: Log in
        client: Anacreon = await Anacreon.log_in(
            game_id="8JNJ7FNZ", 
            username="username",
            password="password"
        )

        ## Step 2: do cool stuff, automatically!
        # find all of our fleets
        all_my_fleets = [
            fleet 
            for fleet in client.space_objects.values()
            if isinstance(fleet, Fleet)
            and fleet.sovereign_id == client.sov_id
        ]

        # send all our fleets to world ID 100
        for fleet in all_my_fleets:
            await client.set_fleet_destination(fleet.id, 100)

    if __name__ == "__main__":
        asyncio.run(main())


Rate Limits
-----------

The API has rate limits which are detailed in 
`this Ministry record <https://ministry.kronosaur.com/record.hexm?id=79981>`_. 
Beware that they apply to both any scripts you write AND the online client.


.. |PyPI Version| image:: https://img.shields.io/pypi/v/anacreonlib.svg
   :target: https://pypi.python.org/pypi/anacreonlib

.. |Documentation Status| image:: https://readthedocs.org/projects/anacreonlib/badge/?version=latest
   :target: http://anacreonlib.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

