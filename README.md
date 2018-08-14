	TEST TASK FOR COMPETERA
------------------------------------------------------------------------------------------
	Application created for processing csv and xml files
	with an addition records in DB as required and ftp-sending
------------------------------------------------------------------------------------------
	Only 2 non-standard solutions were selected.
	1)Processing received csv-s by the form, not by cache, but with saving on disk
	and then removing after all.
	2)Using raw queries in some cases, cuz that was more easiest and faster.
------------------------------------------------------------------------------------------
	The Functional is divided into 6 logical blocks
	1)CSV Processing
	2)Xml Parsing
	3)Merging between csv and xml
	4)Making DB records
	5)Reports creating
	6)Ftp-sending
------------------------------------------------------------------------------------------
	Sqlite3 was used for simplifying transfers between PC's during code writing
------------------------------------------------------------------------------------------
	By the deductive thinking such paragraph as "cost-price" was identified by
	me according to the formula (price-delivery_cost), and such as "color" and "event"
	was ignored to recording into DB, but collected into dict-s.
------------------------------------------------------------------------------------------
	Form sending is completely dependent, i.e file with articles should be sent
	in first form, and with additional information in second.
