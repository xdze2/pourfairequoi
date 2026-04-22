From Wikipedia, the free encyclopedia

[![](https://upload.wikimedia.org/wikipedia/commons/0/0a/Arcadia_logo.png)](https://en.wikipedia.org/wiki/File:Arcadia_logo.png)

ARCADIA, a model-based engineering method for systems, hardware and software architectural design.

**ARCADIA** (**Arc**hitecture **A**nalysis & **D**esign **I**ntegrated **A**pproach) is a [system](https://en.wikipedia.org/wiki/Systems_engineering "Systems engineering") and [software](https://en.wikipedia.org/wiki/Software_engineering "Software engineering") architecture engineering method based on architecture-centric and [model-driven engineering](https://en.wikipedia.org/wiki/Model-driven_engineering "Model-driven engineering") activities.

In the development cycle of a system, former practices focused more on the definition of [requirements](https://en.wikipedia.org/wiki/Requirement "Requirement"), their allocation to each component of the system component and associated traceability. Current approaches rather focus on [functional analysis](https://en.wikipedia.org/wiki/Functional_design "Functional design"), [system design](https://en.wikipedia.org/wiki/Systems_design "Systems design"), justification of architectural choices, and verification steps. In addition, the design takes into account not only the [functional](https://en.wikipedia.org/wiki/Function_model "Function model") point of view, but also other points of view, which affect the definition and breakdown of the system. For example, [constraints](https://en.wikipedia.org/wiki/Constraint_(computer-aided_design) "Constraint (computer-aided design)") relating to system integration, [product line](https://en.wikipedia.org/wiki/Product_lining "Product lining") management, [safety](https://en.wikipedia.org/wiki/Safety "Safety"), [performance](https://en.wikipedia.org/wiki/Performance "Performance") and [feasibility](https://en.wikipedia.org/wiki/Logical_possibility "Logical possibility"). Systems engineering is therefore not just about managing the system requirements, but is a complex design activity.

As an answer to this challenge, the ARCADIA method was created by [Thales](https://en.wikipedia.org/wiki/Thales_Group "Thales Group") in 2007, placing [architecture](https://en.wikipedia.org/wiki/Systems_architecture "Systems architecture") and [collaboration](https://en.wikipedia.org/wiki/Collaboration "Collaboration") at the center of systems engineering practices.

The vision for ARCADIA was to break the "walls" between different engineering specializations including [architects](https://en.wikipedia.org/wiki/Architectural_engineering "Architectural engineering"), development teams, Specialists, [IVVQ](https://en.wikipedia.org/wiki/Integration_testing "Integration testing") (Integration, Verification, Validation, and Qualification) Teams, Customer and external partners.

The ARCADIA method is about to be standardized as an [AFNOR](https://en.wikipedia.org/wiki/AFNOR "AFNOR") experimental norm.<sup id="cite_ref-1"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-1"><span>[</span>1<span>]</span></a></sup> It has been published on March 7, 2018.

The ARCADIA method applies to the design of [complex](https://en.wikipedia.org/wiki/Complex_system "Complex system") and [critical](https://en.wikipedia.org/wiki/Life-critical_system "Life-critical system") systems, and more generally architectures that are subject to multiple [functional and non-functional constraints](https://en.wikipedia.org/wiki/Non-functional_requirement "Non-functional requirement"), including software, electronic, electrical architectures, and industrial processes. It defines a set of practices that guides needs analysis and design to meet an operational requirement. At the same time it is adaptable to the processes and constraints linked to various types of life cycles such as [bottom-up approach](https://en.wikipedia.org/wiki/Top-down_and_bottom-up_design "Top-down and bottom-up design"), application reuse, incremental, iterative and partial development.

## Objectives and action means

\[[edit](https://en.wikipedia.org/w/index.php?title=Arcadia_(engineering)&action=edit&section=4 "Edit section: Objectives and action means")\]

ARCADIA is a structured engineering method to identify and check the architecture of complex systems. It promotes collaborative work among all stakeholders during many of the engineering phases of the system. It allows iterations during the definition phase that help the architects to converge towards satisfaction of all identified needs.

Even if textual requirements are kept as a support for part of customer need capture, ARCADIA favors functional analysis as the major way to formalize the need and solution behavior. This includes operational, functional and non-functional aspects, along with resulting definition of the architecture, based on – and justified against – this functional analysis.

ARCADIA is based on the following general principles:

-   All engineering stakeholders share the same language, method set of engineering artifacts and information, description of the need and the product itself as a shared model;
-   Each set of constraints (e.g. safety, performance, cost, mass, etc.) is formalized in a "viewpoint" against which each candidate architecture will be checked;
-   Architecture verification rules are established and the model is challenged against them, so as to check that architecture definition meets expectations, as early as possible in the process;
-   Co-engineering between the different levels of engineering is supported by the joint development of models. Models of various levels of the architecture and trade-offs are deduced, validated and/or connected with each other.

The ARCADIA method is tooled through [Capella](https://en.wikipedia.org/wiki/Capella_(engineering) "Capella (engineering)"), a modeling tool that meets full-scale deployment constraints in an operational context. Capella is available free of charge from the engineering community under open source.

The ARCADIA method:

-   Covers all structured engineering activities, from capturing customer operational needs to system integration verification validation (IVV);
-   Takes into account multiple engineering levels and their effective collaboration (system, subsystem, software, hardware, etc.);
-   Integrates co-engineering with specialty engineering (safety, security, performance, interfaces, logistics ...) and IVV;
-   Provides the ability not only to share descriptive models but also to collaboratively validate properties of the definition and the architecture;
-   Is field-tested in full-scale industrial applications, and is currently deployed on dozens of major projects in several countries and divisions of Thales.

## Methodological approach

\[[edit](https://en.wikipedia.org/w/index.php?title=Arcadia_(engineering)&action=edit&section=6 "Edit section: Methodological approach")\]

[![Viewpoints](https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/ARCADIA_viewpoints.png/250px-ARCADIA_viewpoints.png)](https://en.wikipedia.org/wiki/File:ARCADIA_viewpoints.png)

Viewpoints

[![Collaboration](https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/ARCADIA_collaboration.png/250px-ARCADIA_collaboration.png)](https://en.wikipedia.org/wiki/File:ARCADIA_collaboration.png)

Collaboration

One of the difficulties frequently encountered in the development of complex systems comes from the superposition of several partially independent functional chains using shared resources (including but not limited to computing resources). The ARCADIA method and the underlying tools are used to identify functional chains, their overlapping scenarios and desired performance, along with their support by the architecture. Starting with the first level of system analysis, they ensure traceability throughout the process definition and check each proposed architectural design against expected performance and constraints.

The non-functional properties expected from the system solution are also formalized in 'viewpoints'. Each viewpoint captures constraints that the system should face or meet (feared events, security threats, latency expectations, product line or reuse constraints, power consumption or cost issues, and more). Then the architecture model is automatically analyzed to verify that it meets these constraints, thanks to dedicated expert rules (performance computation, resource consumption, safety or security barriers, etc.). This analysis can be done very early in the development cycle, detecting design issues as soon as possible ("early validation").

As a summary, the approach to characterization by views (or "viewpoints") cross-checks that the proposed architecture is capable of providing the required functions with the desired level of performance, security, dependability, mass, scalability, environments, mass, interfaces, etc. ensuring the consistency of engineering decisions, because all engineering stakeholders share the same engineering information, and can apply his/her own views and checks to them, so as to secure the common definition.

## Presentation of the approach and key concepts

\[[edit](https://en.wikipedia.org/w/index.php?title=Arcadia_(engineering)&action=edit&section=7 "Edit section: Presentation of the approach and key concepts")\]

The first level views used to elaborate and share the architecture model are described below:

-   "Define the Problem – Customer Operational Need Analysis",

The first step focuses on analysing the customer needs and goals, expected missions and activities, far beyond System/SW requirements. This is expected to ensure good adequacy of System/SW definition with regards to its real operational use – and define IVVQ conditions. Outputs of this step consist mainly in an "operational architecture" describing and structuring this need, in terms of actors/users, their operational capabilities and activities, operational use scenarios giving dimensioning parameters, operational constraints including safety, security, lifecycle, etc.

-   "Formalisation of System/SW Requirements – System/SW Need Analysis",

The second step focuses now on the system/SW itself, in order to define how it can satisfy the former operational need, along with its expected behaviour and qualities: system/SW functions to be supported and related exchanges, non functional constraints (safety, security...), performances allocated to system boundary, role sharing and interactions between system and operators. It also checks for feasibility (including cost, schedule and technology readiness) of customer requirements, and if necessary gives means to renegotiate their contents. To do this, a first early system/SW architecture (architectural design model) is sketched, from system/SW functional need; then requirements are examined against this architecture in order to evaluate their cost and consistency. Outputs of this step mainly consist of system/SW functional Need description, interoperability and interaction with the users and external systems (functions, exchanges plus non-functional constraints), and system/SW requirements.

Note that these two steps, which constitute the first part of Architecture building, "specify" the further design, and therefore should be approved/validated with the customer.

-   "Development of System/SW Architecture – Logical Architecture",

The third step intends to identify the system/SW parts (hereafter called components), their contents, relationships and properties, excluding implementation or technical/technological issues. This constitutes the system/SW logical architecture. In order for this breakdown in components to be stable in further steps, all major \[non-functional\] constraints (safety, security, performance, IVV, Cost, non technical, etc.) are taken into account and compared to each other's so as to find the best compromise between them. This method is described as "Viewpoints-driven", viewpoints being the formalization of the way these constraints impact the system/SW architecture. Outputs of this step consist of the selected logical architecture: components and interfaces definition, including formalization of all viewpoints and the way they are taken into account in the components design. Since the architecture has to be validated against Need, links with requirements and operational scenarios are also produced.

-   "Development of System/SW Architecture – Physical Architecture",

The fourth step has the same intents as logical architecture building, except that it defines the "final" architecture of the system/SW at this level of engineering, ready to develop (by lower engineering levels). Therefore, it introduces rationalization, architectural patterns, new technical services and components, and makes the logical architecture evolve according to implementation, technical and technological constraints and choices (at this level of engineering). Note that the same "Viewpoints-driven" method as for logical architecture building is used for physical architecture definition. Outputs of this step consist of the selected physical architecture: components to be produced, including formalization of all viewpoints and the way they are taken into account in the components design. Links with requirements and operational scenarios are also produced.

-   "Formalize Components Requirements – Contracts for Development and IVVQ",

The fifth and last step is a contribution to EPBS (End-Product Breakdown Structure) building, taking benefits from the former architectural work, to enforce components requirements definition, and prepare a secured IVVQ. All choices associated to the system/SW chosen architecture, and all hypothesis and constraints imposed to components and architecture to fit need and constraints, are summarized and checked here. Outputs from this step are mainly "component Integration contract" collected all necessary expected properties for each component to be developed.

The following figure shows a global view summarizing the recommended technical process, featuring the three elements of the engineering triptych, and their production activities all along the definition and design process.

As part of the Clarity Project, a book on the ARCADIA method will be published. An introductory document is currently available for download on the Capella website.<sup id="cite_ref-2"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-2"><span>[</span>2<span>]</span></a></sup>

The ARCADIA method was presented at various events:

| Conference | Title | Date | Place |
| --- | --- | --- | --- |
| MODELS'16 | ARCADIA in a nutshell<sup id="cite_ref-3"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-3"><span>[</span>3<span>]</span></a></sup> | 02/10/2016 | [Saint Malo](https://en.wikipedia.org/wiki/Saint_Malo "Saint Malo") |
| [INCOSE International Symposium](https://en.wikipedia.org/w/index.php?title=INCOSE_International_Symposium&action=edit&redlink=1 "INCOSE International Symposium (page does not exist)") | Implementing the MBSE Cultural Change: Organization, Coaching and Lessons Learned<sup id="cite_ref-4"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-4"><span>[</span>4<span>]</span></a></sup> | 14/07/2015 | [Seattle](https://en.wikipedia.org/wiki/Seattle "Seattle") |
| INCOSE International Symposium | From initial investigations up to large-scale rollout of an MBSE method and its supporting workbench: the Thales experience<sup id="cite_ref-5"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-5"><span>[</span>5<span>]</span></a></sup> | 14/07/2015 | [Seattle](https://en.wikipedia.org/wiki/Seattle "Seattle") |
| [EclipseCon](https://en.wikipedia.org/wiki/EclipseCon "EclipseCon") France | Systems Modeling with the ARCADIA method and the Capella tool<sup id="cite_ref-6"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-6"><span>[</span>6<span>]</span></a></sup> | 24/06/2015 | [Toulouse](https://en.wikipedia.org/wiki/Toulouse "Toulouse") |
| Model-Based System Engineering (MBSE) Symposium | The Challenges of Deploying MBSE Solutions<sup id="cite_ref-7"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-7"><span>[</span>7<span>]</span></a></sup> | 28/10/2014 | [Canberra](https://en.wikipedia.org/wiki/Canberra "Canberra") |
| Model-Based System Engineering (MBSE) Symposium | Arcadia and Capella in the Field<sup id="cite_ref-8"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-8"><span>[</span>8<span>]</span></a></sup> | 27/10/2014 | [Canberra](https://en.wikipedia.org/wiki/Canberra "Canberra") |
| EclipseCon France | Arcadia / Capella, a field-proven modeling solution for system and software architecture engineering<sup id="cite_ref-9"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-9"><span>[</span>9<span>]</span></a></sup> | 19/06/2014 | [Toulouse](https://en.wikipedia.org/wiki/Toulouse "Toulouse") |
| MDD4DRES ENSTA Summer school | Feedbacks on System Engineering – ARCADIA, a model-based method for Architecture-centric Engineering<sup id="cite_ref-10"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-10"><span>[</span>10<span>]</span></a></sup> | 01/09/2014 | [Aber Wrac'h](https://en.wikipedia.org/wiki/Aber_Wrac%27h "Aber Wrac'h") |
| EclipseCon North America | Arcadia / Capella, a field-proven modeling solution for system and software architecture engineering<sup id="cite_ref-11"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-11"><span>[</span>11<span>]</span></a></sup> | 20/03/2015 | [San Francisco](https://en.wikipedia.org/wiki/San_Francisco "San Francisco") |
| Complex Systems Design & Management (CSDM) | ARCADIA: Model-Based Collaboration for System, Software and Hardware Engineering<sup id="cite_ref-12"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-12"><span>[</span>12<span>]</span></a></sup> | 04/12/2013 | [Paris](https://en.wikipedia.org/wiki/Paris "Paris") |
| Congrès Ingénierie grands programmes et systèmes complexes | La modélisation chez Thales : un support majeur à la collaboration des acteurs dans l’ingénierie des grands systèmes<sup id="cite_ref-13"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-13"><span>[</span>13<span>]</span></a></sup> | 10/06/2013 | [Arcachon](https://en.wikipedia.org/wiki/Arcachon "Arcachon") |
| MAST | Toward integrated multi-level engineering - Thales and DCNS advanced Practices<sup id="cite_ref-14"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-14"><span>[</span>14<span>]</span></a></sup> | 04/06/2013 | [Gdańsk](https://en.wikipedia.org/wiki/Gda%C5%84sk "Gdańsk") |
| CSDM | Modelling languages for Functional Analysis put to the test of real life<sup id="cite_ref-15"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-15"><span>[</span>15<span>]</span></a></sup> | 2012 | [Paris](https://en.wikipedia.org/wiki/Paris "Paris") |
| ICAS | Method and tools to secure and support collaborative architecting of constrained systems<sup id="cite_ref-16"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-16"><span>[</span>16<span>]</span></a></sup> | 2010 | [Nice](https://en.wikipedia.org/wiki/Nice "Nice") |
| CSDM | Model-driven Architecture building for constrained Systems<sup id="cite_ref-17"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-17"><span>[</span>17<span>]</span></a></sup> | 2010 | [Paris](https://en.wikipedia.org/wiki/Paris "Paris") |
| INCOSE;08 Symposium | Method & Tools for constrained System Architecting<sup id="cite_ref-18"><a href="https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_note-18"><span>[</span>18<span>]</span></a></sup> | 2008 | [Utrecht](https://en.wikipedia.org/wiki/Utrecht "Utrecht") |

-   [Metamodeling](https://en.wikipedia.org/wiki/Metamodeling "Metamodeling")
-   [Model-driven engineering](https://en.wikipedia.org/wiki/Model-driven_engineering "Model-driven engineering")

1.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-1 "Jump up")** ["Norme PR XP Z67-140 | Norm'Info"](https://norminfo.afnor.org/norme/pr-xp-z67-140/technologies-de-linformation-arcadia-methode-pour-lingenierie-des-systemes-soutenue-par-son-langage-de-modelisation/123795). _norminfo.afnor.org_ (in French). Retrieved 2018-02-01.
2.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-2 "Jump up")** ["ARCADIA introductory document"](https://www.polarsys.org/capella/arcadia.html). Retrieved 2015-10-23.
3.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-3 "Jump up")** ["ARCADIA in a nutshell"](http://models2016.irisa.fr/tutorials/). Retrieved 2016-10-06.
4.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-4 "Jump up")** ["Implementing the MBSE Cultural Change: Organization, Coaching and Lessons Learned"](https://web.archive.org/web/20160303204501/http://events.incose.org/sessiondetail_928). Archived from [the original](http://events.incose.org/sessiondetail_928) on 2016-03-03. Retrieved 2015-10-23.
5.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-5 "Jump up")** ["From initial investigations up to large-scale rollout of an MBSE method and its supporting workbench: the Thales experience"](https://web.archive.org/web/20160303203940/http://events.incose.org/sessiondetail_916). Archived from [the original](http://events.incose.org/sessiondetail_916) on 2016-03-03. Retrieved 2015-10-23.
6.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-6 "Jump up")** ["Systems Modeling with the ARCADIA method and the Capella tool"](https://web.archive.org/web/20150914171138/https://www.eclipsecon.org/france2015/session/systems-modeling-arcadia-method-and-capella-tool). Archived from [the original](https://www.eclipsecon.org/france2015/session/systems-modeling-arcadia-method-and-capella-tool) on 2015-09-14. Retrieved 2015-10-23.
7.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-7 "Jump up")** ["The Challenges of Deploying MBSE Solutions"](https://web.archive.org/web/20160228102023/http://sesa.org.au/downloads-usermenu-33/doc_download/420-the-challenges-of-deploying-mbse-solutions-introduction). Archived from [the original](http://www.sesa.org.au/downloads-usermenu-33/doc_download/420-the-challenges-of-deploying-mbse-solutions-introduction) on 2016-02-28. Retrieved 2015-10-23.
8.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-8 "Jump up")** ["Arcadia and Capella in the Field"](https://web.archive.org/web/20160228102228/http://sesa.org.au/downloads-usermenu-33/doc_download/406-arcadia-and-capella-in-the-field). Archived from [the original](http://www.sesa.org.au/downloads-usermenu-33/doc_download/406-arcadia-and-capella-in-the-field) on 2016-02-28. Retrieved 2015-10-23.
9.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-9 "Jump up")** ["Arcadia / Capella, a field-proven modeling solution for system and software architecture engineering"](https://www.eclipsecon.org/france2014/session/arcadia-capella-field-proven-modeling-solution-system-and-software-architecture-engineering). Retrieved 2015-10-23.`{{[cite web](https://en.wikipedia.org/wiki/Template:Cite_web "Template:Cite web")}}`: CS1 maint: deprecated archival service ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_deprecated_archival_service "Category:CS1 maint: deprecated archival service"))
10.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-10 "Jump up")** ["Feedbacks on System Engineering – ARCADIA"](http://www.mdd4dres.org/program/#JL). Retrieved 2015-10-22.
11.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-11 "Jump up")** ["Arcadia / Capella, a field-proven modeling solution for system and software architecture engineering"](https://web.archive.org/web/20160303183801/https://www.eclipsecon.org/na2014/session/arcadia-capella-field-proven-modeling-solution-system-and-software-architecture-engineering). Archived from [the original](https://www.eclipsecon.org/na2014/session/arcadia-capella-field-proven-modeling-solution-system-and-software-architecture-engineering) on 2016-03-03. Retrieved 2015-10-23.
12.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-12 "Jump up")** ["Model-Based Collaboration for System, Software and Hardware Engineering"](http://www.csdm2013.csdm.fr/-Program-.html). Retrieved 2015-10-23.
13.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-13 "Jump up")** ["La modélisation chez Thales : un support majeur à la collaboration des acteurs dans l'ingénierie des grands systèmes"](https://web.archive.org/web/20160303170952/http://www.avantage-aquitaine.com/conferences/ingenierie13/assets/pdf/Programme%20IGPSC%20ed8.pdf) (PDF). Archived from [the original](http://www.avantage-aquitaine.com/conferences/ingenierie13/assets/pdf/Programme%20IGPSC%20ed8.pdf) (PDF) on 2016-03-03. Retrieved 2015-10-23.
14.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-14 "Jump up")** ["Toward integrated multi-level engineering - Thales and DCNS advanced Practices"](http://lanyrd.com/2013/mastconfex/scftxc/). Retrieved 2015-10-23.
15.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-15 "Jump up")** Voirin, Jean-Luc (2013). "Modelling Languages for Functional Analysis Put to the Test of Real Life". _Complex Systems Design & Management_. pp. 139–150\. [doi](https://en.wikipedia.org/wiki/Doi_(identifier) "Doi (identifier)"):[10.1007/978-3-642-34404-6\_9](https://doi.org/10.1007%2F978-3-642-34404-6_9). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier) "ISBN (identifier)") [978-3-642-34403-9](https://en.wikipedia.org/wiki/Special:BookSources/978-3-642-34403-9 "Special:BookSources/978-3-642-34403-9").
16.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-16 "Jump up")** ["Method and tools to secure and support collaborative architecting of constrained systems"](https://www.icas.org/ICAS_ARCHIVE/ICAS2010/ABSTRACTS/172.HTM). Retrieved 2015-10-23.
17.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-17 "Jump up")** ["Model-driven Architecture building for constrained Systems"](https://web.archive.org/web/20160303170640/http://www.cesames.net/fichier.php?id=291). Archived from [the original](http://www.cesames.net/fichier.php?id=291) on 2016-03-03. Retrieved 2015-10-23.
18.  **[^](https://en.wikipedia.org/wiki/Arcadia_(engineering)#cite_ref-18 "Jump up")** Voirin, Jean-Luc (2008). "Method & Tools for constrained System Architecting". _INCOSE International Symposium_. **18**: 981–995\. [doi](https://en.wikipedia.org/wiki/Doi_(identifier) "Doi (identifier)"):[10.1002/j.2334-5837.2008.tb00857.x](https://doi.org/10.1002%2Fj.2334-5837.2008.tb00857.x). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier) "S2CID (identifier)") [111113361](https://api.semanticscholar.org/CorpusID:111113361).

-   [Web page dedicated to the method](https://www.eclipse.org/capella/arcadia.html)
-   [Official forum](https://www.eclipse.org/forums/index.php/f/506/)
-   [Thales, founder of the method](https://www.thalesgroup.com/)