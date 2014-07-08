--
-- Data for Name: arch; Type: TABLE DATA; Schema: public; Owner: reedstrm
--

COPY arch (id, name) FROM stdin;
4	ipad
5	mobile
9	desktop
10	kindle
12	any
\.


--
-- Data for Name: distribution; Type: TABLE DATA; Schema: public; Owner: reedstrm
--

COPY distribution (id, name) FROM stdin;
2	cnx
3	ccap
4	openstax
\.


--
-- Data for Name: format; Type: TABLE DATA; Schema: public; Owner: reedstrm
--

COPY format (id, name) FROM stdin;
2	pdf
3	epub
4	mobi
5	completezip
\.

--
-- Data for Name: status; Type: TABLE DATA; Schema: public; Owner: reedstrm
--

COPY status (id, name) FROM stdin;
1	Waiting
2	Blocked
3	Cancelled
4	Building
5	Failed
6	Uploaded
7	Done
\.


--
-- Data for Name: suite; Type: TABLE DATA; Schema: public; Owner: reedstrm
--

COPY suite (id, name) FROM stdin;
3	latex
4	princexml
\.


--
-- Data for Name: suitearches; Type: TABLE DATA; Schema: public; Owner: reedstrm
--

COPY suitearches (id, suite_id, arch_id) FROM stdin;
6	3	9
7	4	9
8	4	5
\.
