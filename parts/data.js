/* ================================================================
   Content. Every fact about XRLibraries comes from a public source listed in SOURCES.
   ================================================================ */
const SOURCES = {
  about:{ label:'xrlibraries.com/about', url:'https://www.xrlibraries.com/about' },
  home:{ label:'xrlibraries.com', url:'https://www.xrlibraries.com/' },
  equity:{ label:'xrlibraries.com/equity-diversity', url:'https://www.xrlibraries.com/equity-diversity' },
  metaverse:{ label:'xrlibraries.com/metaverse', url:'https://www.xrlibraries.com/metaverse' },
  environment:{ label:'xrlibraries.com/environment', url:'https://www.xrlibraries.com/environment' },
  fair:{ label:'xrlibraries.com/mcf2025', url:'https://www.xrlibraries.com/mcf2025' },
  showcase:{ label:'xrlibraries.com/xr-showcase', url:'https://www.xrlibraries.com/xr-showcase' },
  playbooks:{ label:'xrlibraries.com/xr-playbooks', url:'https://www.xrlibraries.com/xr-playbooks' },
  sjsu:{ label:'SJSU School of Information', url:'https://ischool.sjsu.edu/xrlibraries' },
  arbor:{ label:'ArborXR customer story', url:'https://arborxr.com/blog/how-arborxr-helped-xr-libraries-scale-save-time-on-content-management-for-virtual-reality/' },
  arborPod:{ label:'ArborXR podcast, 2025', url:'https://arborxr.com/podcast/michelle-rebaleati-powering-nevadas-statewide-vr-career-training-with-1000-devices-across-80-locations' },
  working:{ label:'WorkingNation, 2023', url:'https://workingnation.com/?p=84615' },
  cil:{ label:'Computers in Libraries speaker page', url:'https://computersinlibraries.infotoday.com/2023/27335-John-MacLeod.aspx' },
  wsl:{ label:'Washington State Library, VR 360', url:'https://washstatelib.libguides.com/vr360/overview' },
  cb:{ label:'CB Insights company profile', url:'https://www.cbinsights.com/company/xr-libraries/' },
  cenic:{ label:'CENIC, 2019', url:'https://cenic.org/blog/cenic-helps-to-power-virtual-reality' },
  lj2017:{ label:'Library Journal, 2017', url:'https://libraryjournal.com/story/oculus-virtual-reality-tech-rolls-california-libraries' },
  lj2019:{ label:'Library Journal, 2019', url:'https://www.libraryjournal.com/story/nevada-state-library-enters-new-phase-of-virtual-reality-project' },
  vive2018:{ label:'HTC VIVE news release, 2018', url:'https://www.vive.com/us/newsroom/2018-09-06-3/' },
  carson2018:{ label:'Carson Now, 2018', url:'https://carsonnow.org/story/02/17/2018/virtual-reality-stations-featured-carson-city-library-re-opening-celebration' },
  goed2023:{ label:'Nevada GOED, 2023', url:'https://goed.nv.gov/virtual-reality-course-part-of-worlds-largest-library-catalog' },
  sjsu2024:{ label:'SJSU School of Information news, 2024', url:'https://ischool.sjsu.edu/news/virtual-reality-exhibit-gives-voice-ukrainian-children-and-librarians' }
};

const GALLERIES = [
  { label:'Lobby', name:'XRLibraries Campus', years:'Start here', z0:0, z1:-6, wall:0xd6cbb6 },
  { label:'Gallery 1 of 3', name:'Headsets in Libraries', years:'2016 to 2022', z0:-6, z1:-18, wall:0x1f3d3a },
  { label:'Gallery 2 of 3', name:'Learning That Works', years:'Careers and resources', z0:-18, z1:-30, wall:0x22304f },
  { label:'Gallery 3 of 3', name:'Stories Worth Saving', years:'Equity, worlds, nature', z0:-30, z1:-42, wall:0x3e1f2c }
];
const KIND = { milestone:'Milestone', mission:'Mission', object:'Object', event:'Event', program:'Program', story:'Story', resource:'Resource', project:'Project', reenactment:'Living History' };

const ITEMS = [
  { id:'ca-200', g:1, kind:'milestone', title:'Over 200 VR Systems in California Libraries', date:'2016', year:2016,
    where:'California public libraries', partners:'', src:['about'],
    desc:'XRLibraries began in 2016 by installing more than 200 virtual reality systems in California public libraries. Its website calls this the largest VR installation in public libraries.',
    place:{wall:'L', z:-9}, size:[1.5,1.05], art:{ type:'bignum', num:'200+', l1:'VR systems', l2:'in California public libraries', kick:'2016 · WHERE IT STARTED', motif:'grid', bg:'#173230' } },
  { id:'mission', g:1, kind:'mission', title:'XR Made Easy for Everyone', date:'Since 2016', year:null,
    where:'Libraries and schools', partners:'', src:['about','sjsu'],
    desc:'XRLibraries works with schools and libraries to bring virtual, augmented and mixed reality into their programs and classes. Its stated goal is equitable access to immersive technology for all communities.',
    quote:'We make XR easy to use for everyone.', quoteBy:'XRLibraries, on its About page',
    place:{wall:'R', z:-9}, size:[1.5,1.05], art:{ type:'quote', bg:'#1f3d3a' } },
  { id:'headset', g:1, kind:'object', title:'A Library VR Headset', date:'Today', year:null,
    where:'Library program rooms', partners:'Meta Quest and Pico are listed partners', src:['home','arbor'],
    desc:'Standalone headsets let a library visitor stand on the moon, swim a coral reef or practice a job, with no computer attached. Meta Quest and Pico both appear on XRLibraries’ partner list, and its Nevada headsets run on Pico.',
    place:{wall:'P', x:-2.6, z:-12}, object:'headset', art:{ type:'headset' } },
  { id:'nv-2017', g:1, kind:'milestone', title:'Nevada Follows Marin County', date:'2017', year:2017,
    where:'Nevada public libraries', partners:'Nevada State Library', src:['working'],
    desc:'In 2017 Nevada’s state library put its first VR headsets in public libraries: 22 headsets in 11 libraries, with STEM content. WorkingNation reports that the model followed a program at the Marin County Free Library in California.',
    place:{wall:'L', z:-15}, size:[1.5,1.05], art:{ type:'bignum', num:'22', l1:'headsets in 11 libraries', l2:'Nevada’s first phase', kick:'2017 · NEVADA', motif:'nevada', dots:11, bg:'#1d2f3a' } },
  { id:'cil-talks', g:1, kind:'event', title:'XR at Computers in Libraries', date:'2020 and 2022', year:2020,
    where:'Computers in Libraries conference', partners:'Information Today', src:['cil'],
    desc:'XRLibraries’ executive director, John MacLeod, presented “Integrating XR Tech & Programming in Libraries” at Computers in Libraries Connect in 2020 and “Using XR to Discover ‘Lost Stories’ & Pop-Up Books” in 2022.',
    place:{wall:'R', z:-15}, size:[1.0,1.32], art:{ type:'badge' } },

  { id:'sandi', g:2, kind:'program', title:'Project SANDI', date:'Began in 2020', year:2020,
    where:'Nevada', partners:'Nevada Governor’s Office of Economic Development, XRLibraries', src:['working','arborPod','about'],
    desc:'Supporting and Advancing Nevada’s Dislocated Individuals began during the 2020 downturn with a $13.8 million federal grant. It uses VR to explore careers in five fields: skilled trades, healthcare, IT, advanced manufacturing and logistics.',
    more:'The program grew to more than 1,000 headsets at over 80 locations, with 35 VR field trips and five training simulations, including dialysis technician and certified nursing assistant. XRLibraries’ executive director is a partner in the project.',
    place:{wall:'L', z:-21}, size:[1.5,1.05], art:{ type:'sectors' } },
  { id:'nv-1100', g:2, kind:'milestone', title:'1,100 Headsets in Nevada', date:'2020s', year:null,
    where:'Nevada community college and public libraries', partners:'Lifeliqe, ArborXR', src:['home','arbor'],
    desc:'XRLibraries and Lifeliqe installed VR headsets in Nevada’s community college and public libraries. XRLibraries’ homepage counts more than 1,100.',
    more:'XRLibraries uses ArborXR to set up headsets and send updates remotely. Its director told ArborXR the switch cut the time and resources spent by about 60 percent.',
    place:{wall:'R', z:-21}, size:[1.5,1.05], art:{ type:'bignum', num:'1,100+', l1:'VR headsets', l2:'in Nevada college and public libraries', kick:'NEVADA · STATEWIDE', motif:'nevada', dots:70, bg:'#1f2a44' } },
  { id:'dialysis', g:2, kind:'story', title:'Training From a Town of 300', date:'2020s', year:null,
    where:'Rural Nevada', partners:'College of Southern Nevada', src:['arbor','working'],
    desc:'A remote 12-week dialysis technician certification lets people train without traveling to a training center. In a community of about 300 people, a single mother finished the program, passed her certification and plans to become a registered nurse.',
    quote:'It brought the dialysis concepts to life.', quoteBy:'Natasha York, former library assistant, in WorkingNation',
    place:{wall:'L', z:-27}, size:[1.15,1.15], art:{ type:'story' } },
  { id:'playbooks', g:2, kind:'resource', title:'XR Playbooks', date:'Ongoing', year:null,
    where:'Pre-installed on library headsets', partners:'', src:['sjsu','playbooks'],
    desc:'XRLibraries catalogs more than 300 XR apps in categories from astronomy and history to mindfulness and music, then bundles them into themed playbooks that come pre-installed on library headsets.',
    place:{wall:'P', x:-2.6, z:-24}, object:'book', art:{ type:'playbook' } },
  { id:'showcase', g:2, kind:'resource', title:'XR Showcase', date:'Video series', year:null,
    where:'Online', partners:'Hosts George and Camila', src:['showcase'],
    desc:'In this video series, hosts George and Camila try VR and AR apps for libraries, from Tilt Brush and Wander to Apollo 11 VR, and share practical tips like cleaning headsets and setting a guardian boundary.',
    more:'Episodes also cover running big VR events with rotating stations, recording video inside a headset and playing media through the Meta Quest TV app.',
    place:{wall:'R', z:-27}, size:[1.15,1.15], art:{ type:'episodes' } },

  { id:'way-out', g:3, kind:'project', title:'A Way Out of No Way', date:'Lost Stories project', year:null,
    where:'Marin City, California', partners:'The Marinovators, Marin City youth', src:['equity','home'],
    desc:'Marin City students who call themselves the Marinovators built a VR experience of the World War II shipyards and life in Marin City, plus a musical tribute to the African-American workers whose stories were rarely told.',
    more:'The project ran in three tracks: immersive storytelling, music and VR modeling. It is part of XRLibraries’ Lost Stories work, which plans to look for Latino, Asian-Pacific and Native American stories next.',
    place:{wall:'L', z:-33}, size:[1.5,1.05], art:{ type:'shipyard' } },
  { id:'charleston', g:3, kind:'project', title:'The Black Wall Street of Charleston', date:'AR scavenger hunt', year:null,
    where:'Charleston, South Carolina', partners:'Burke High School CTE students, Preservation Society of Charleston, Burke High School Foundation', src:['equity','home'],
    desc:'Career and technical education students at Burke High School built an augmented-reality scavenger hunt that leads players to Charleston’s Black-owned businesses.',
    place:{wall:'R', z:-33}, size:[1.0,1.32], art:{ type:'armap' } },
  { id:'seeking', g:3, kind:'project', title:'Seeking Immortality', date:'Browser-based world', year:null,
    where:'Northern Cheyenne Tribe', partners:'Northern Cheyenne Tribe, SJSU School of Information', src:['metaverse'],
    desc:'A browser-based VR world, funded by an IMLS Native American Enhancement Grant, that preserves endangered Cheyenne language and cultural knowledge. Tribal members and students learned 3D scanning so the tribe keeps control of its own data.',
    place:{wall:'L', z:-39}, size:[1.5,1.05], art:{ type:'scan' } },
  { id:'ukraine', g:3, kind:'project', title:'Children Draw War, Not Flowers', date:'3D art exhibition', year:null,
    where:'Cherkasy region, Ukraine', partners:'SJSU School of Information, Ukrainian librarians, children and veterans, 40 regional libraries', src:['metaverse'],
    desc:'An immersive 3D exhibition of art by children in Ukraine’s Cherkasy region, which took in more than 42,000 displaced children. It helps children work through war-related trauma, preserves their artwork, and was honored at the Anthem Awards.',
    place:{wall:'R', z:-39}, size:[1.15,1.15], art:{ type:'drawings' } },
  { id:'pollinators', g:3, kind:'event', title:'Pollinators at the Marin County Fair', date:'2025', year:2025,
    where:'Marin County Fair, California', partners:'Artist Cynthia Jensen', src:['fair'],
    desc:'At XRLibraries’ bug-themed booth, fairgoers used an AR app called Pollinators to plant flowers and release monarch butterflies that flew around pollinating them. Marin artist Cynthia Jensen lent bug sculptures for the booth.',
    place:{wall:'E', x:-3.6}, size:[1.7,1.7], art:{ type:'pollinators' } }
];
const ITEM = {}; ITEMS.forEach((it) => ITEM[it.id] = it);
const FREEDOM = { id:'freedom', kind:'project', title:'Freedom to Read', date:'A shared world on FrameVR', year:null,
  where:'Online, in the browser', partners:'SJSU School of Information, Unite Against Book Bans, Little Free Library, Books Unbanned', src:['metaverse'],
  desc:'A VR environment that helps citizens, librarians and students fight book bans, and helps young people in affected areas find challenged books that reflect their lives. It is one of the shared worlds listed on XRLibraries’ metaverse page.',
  art:{ type:'freedom' } };

/* Facts the staff know, beyond the exhibits */
const FACTS = [
  { id:'what', src:['about','sjsu','cb'], text:'XRLibraries brings virtual, augmented and mixed reality into libraries and schools. Its stated goal is equitable access to immersive technology for all communities. It began in 2016 and is based in Novato, in Marin County, California.' },
  { id:'who', src:['sjsu','cil'], text:'John MacLeod is the executive director of XRLibraries. He works with state and local libraries on plans for virtual reality, augmented reality and 360 video, and he is building a national clearinghouse where libraries can share XR best practices.' },
  { id:'team', src:['about'], text:'The XRLibraries About page lists John MacLeod as executive director, Dane Lancaster of PacificXR, who led the setup of XRMarin as an immersive learning lab, and George Lightfoot and Camila Oates, the XR Showcase team.' },
  { id:'wsl', src:['wsl'], text:'XRLibraries was the trainer for the Washington State Library’s VR 360 grant program, which in 2022 helped six libraries create 360-degree virtual reality stories about topics important to their communities. The program was funded by IMLS through the Library Services and Technology Act and was open to public, tribal and academic libraries.' },
  { id:'freedom', src:['metaverse'], text:'Freedom to Read is a VR environment built with the SJSU School of Information, Unite Against Book Bans, Little Free Library and Books Unbanned. It helps people fight book bans and helps young people find challenged books that reflect their lives.' },
  { id:'environment', src:['environment'], text:'XRLibraries’ environment projects include the Stanford Ocean Experience, a VR experience about ocean acidification; a Climate Change Playbook of VR apps for viewing and discussion; and Hydrous, which takes visitors to the coral reefs of Palau.' },
  { id:'partners', src:['home'], text:'Partners listed on xrlibraries.com include Meta Quest, Pico, Hydrous, the Washington, Nevada and California state libraries, ALA, Internet Librarian, the Marin County Office of Education, XRMarin, New Media Learning, FastForward and the SJSU School of Information.' },
  { id:'sjsu', src:['sjsu'], text:'XRLibraries is a strategic partner of the Library Technology Integration Lab at the San José State University School of Information.' },
  { id:'xrmarin', src:['cil','about'], text:'XRMarin is an immersive learning lab and academy for creating XR content in Marin County. XRLibraries’ director is a partner in the Marinovation Learning Center and the XRMarin academy.' },
  { id:'concept', src:[], text:'This campus is an unofficial concept made by Ev Holt with Walk the Archive for XRLibraries. Its facts come from public sources such as xrlibraries.com, the SJSU School of Information, WorkingNation and ArborXR.' },
  { id:'yard', src:[], text:'The campus’s Recess Yard has three made-up rides for fun in XR: the Comet Coaster roller coaster, the Sky Drop tower and the Ocean Dive, a guided swim with sea creatures. Visitors can also hunt for hidden XR tokens and unlock badges.' },
  { id:'school', src:[], text:'The campus’s Workshop School has four hands-on rooms. Room 101 is the 3D Art Studio, where you paint and stamp shapes in the air. Room 102 is the Science Lab, with a sieve analysis of sand, an acid–base titration and a pendulum. Room 103 is the Blueprint Lab, with blueprints of a car, an excavator, a house, a truss bridge and a computer, and a bench for building models. Room 104 is the World Builder Studio, which shows how a 3D world like this campus gets made.' },
  { id:'wax', src:['cenic', 'lj2019', 'lj2017'], text:'The museum’s Wax Hall, through the doorway at the end of Gallery 3, is a living-history wing. Twelve scenes of wax figures act out XRLibraries’ story in date order, from the first VR stations in Marin County’s libraries in 2016 to the Pollinators booth at the 2025 Marin County Fair. Each scene comes to life when you walk up to it. The figures are reenactors made for this concept, not likenesses of real people.' },
  { id:'history', src:['cenic', 'lj2017', 'lj2019', 'vive2018', 'goed2023', 'wsl', 'fair'], text:'XRLibraries began in 2016 as the coordinator of the California Virtual Reality Experience, which piloted VR stations in Marin County’s libraries. In 2017 the project spread to more than 90 California libraries, and a pilot in Nevada followed. Later milestones include Nevada’s first VR records in WorldCat in 2019, Project SANDI in 2020, 360-degree storytelling training in Washington in 2022 and the Pollinators AR booth at the 2025 Marin County Fair.' },
  { id:'wta', src:[], text:'Walk the Archive is Ev Holt’s tool for turning a library’s, museum’s or tribe’s collection into a place you can walk through in a web browser, on a phone, a laptop or a library computer.' }
];

/* Library: eight sections, one per stack */
const SUBJECTS = [
  { id:'basics', name:'XR Basics', side:'N', slot:0, color:'#1d3b52' },
  { id:'programs', name:'Library Programs', side:'N', slot:1, color:'#2f4a33' },
  { id:'careers', name:'Careers', side:'N', slot:2, color:'#5a3b22' },
  { id:'story', name:'Storytelling', side:'N', slot:3, color:'#6e2a22' },
  { id:'equity', name:'Lost Stories', side:'S', slot:0, color:'#5e1f2c' },
  { id:'environment', name:'Environment', side:'S', slot:1, color:'#2a5555' },
  { id:'worlds', name:'Shared Worlds', side:'S', slot:2, color:'#3b3550' },
  { id:'tech', name:'Technology', side:'S', slot:3, color:'#24324f' }
];
const SUBJ = {}; SUBJECTS.forEach((s) => SUBJ[s.id] = s);

const BOOKS = [
  { id:'what-is-xr', subject:'basics', icon:'headset', title:'What Is XR?', sub:'Virtual, augmented and mixed reality', pages:[
    { h:'Four kinds of reality', b:[
      'Extended reality, or XR, is the umbrella word for technology that blends computer-made worlds with the one around you. It covers virtual reality, augmented reality and mixed reality.',
      'Each one changes how much of the real world you still see. Picture a dial that runs from the room you are standing in all the way to a completely made-up place.' ] },
    { h:'Virtual reality', b:[
      'Virtual reality, or VR, replaces everything you see with a computer-made world. A headset shows a slightly different picture to each eye, which tricks your brain into seeing depth.',
      'Modern standalone headsets track your head and hands, so you can lean, crouch and reach inside a small play space. One of the first head-mounted displays, built by Ivan Sutherland in 1968, was so heavy it hung from the ceiling.' ] },
    { h:'Augmented and mixed reality', b:[
      'Augmented reality, or AR, adds digital things to your view of the real world, usually through a phone camera. Seeing a dinosaur in your living room through your phone is AR.',
      'Mixed reality goes a step further: digital objects understand the room, so a virtual ball can bounce off your real table. Many headsets now use passthrough cameras to show your room with digital objects added.' ] },
    { h:'360 video', b:[
      'A 360 video is filmed in every direction at once by a camera with two or more lenses. Viewers can look anywhere, but they cannot walk around inside the scene, because the camera recorded from one spot.',
      'That makes 360 video a great way to visit a historic site, a cultural event or a workplace from a library chair, and it is much easier to make than a full 3D world.' ] },
    { h:'Why libraries?', b:[
      'A good headset costs hundreds of dollars, and many people have never tried one. Libraries can give everyone a turn, with help from staff who know the equipment.',
      'XR in libraries is not just games. People use it to explore careers, travel to places they cannot reach, save local stories and learn to make immersive media of their own.' ] }
  ]},
  { id:'ar-around-town', subject:'basics', icon:'phone', title:'AR Around Town', sub:'Scavenger hunts, fairs and pop-up books', pages:[
    { h:'Digital layers on the real world', b:[
      'Augmented reality adds pictures, sounds and information to the real world, usually through a phone camera. Unlike VR, you stay connected to the place around you.',
      'That makes AR great for walking tours, scavenger hunts, outdoor events and books that pop off the page. XRLibraries’ XR Showcase features LP Bookspace, AR books with friendly characters that explain the story and quiz readers.' ] },
    { h:'The Black Wall Street of Charleston', b:[
      'Career and technical education students at Burke High School in Charleston, South Carolina, built an AR scavenger hunt featuring Charleston’s Black-owned businesses.',
      'Partners included the Preservation Society of Charleston and the Burke High School Foundation. The hunt works as a history lesson and as a way to support local businesses.' ] },
    { h:'Pollinators at the fair', b:[
      'At the 2025 Marin County Fair, XRLibraries’ bug-themed booth featured Pollinators, an AR app where fairgoers planted flowers and released monarch butterflies that flew around pollinating them.',
      'Videos about butterfly migration and pollination, and bug sculptures by Marin artist Cynthia Jensen, rounded out the booth.' ] },
    { h:'Design an AR hunt', b:[
      'Choose five to eight stops that tell one story. Research each stop, then write a short clue and a fun fact for each one.',
      'Ask business owners and property managers for permission, and pick a route with safe sidewalks and crossings.' ] },
    { h:'Test it outside', b:[
      'Walk the route at different times of day. GPS can drift near tall buildings, and screens can be hard to read in bright sun.',
      'Remind players to look up from their phones while they walk. The best AR adds to the real world without making people forget it is there.' ] }
  ]},
  { id:'vr-program', subject:'programs', icon:'checklist', title:'Running a VR Program', sub:'A starter guide for libraries', pages:[
    { h:'Start with a goal', b:[
      'A VR program works best when it has a purpose: exploring careers, visiting the ocean floor, learning history or making art. Pick a theme, then choose a few apps that fit it.',
      'XRLibraries groups apps into themed playbooks so a librarian can run a program on day one. Its catalog covers categories like astronomy, history, life science, travel, mindfulness and music.' ] },
    { h:'Before the first visitor', b:[
      'Charge every headset and test each app. Clear a play area of tables, cords and walls, and set the guardian boundary, the virtual fence that warns players before they bump into something.',
      'Plan how others will watch. Casting the headset view to a TV lets a group follow along, and it keeps the person in the headset from feeling alone.' ] },
    { h:'Keep it clean', b:[
      'Headsets touch faces, so clean them between users. XRLibraries’ XR Showcase episodes show how to sanitize headsets and use UV cleaning devices, which matters in any public setting.',
      'Face covers and wipes at every station make cleaning part of the routine instead of an afterthought.' ] },
    { h:'Welcoming new users', b:[
      'Many visitors have never worn a headset. Start them with something calm and seated, show them how to adjust the fit, and stay close as a spotter.',
      'Keep first sessions short. If someone feels dizzy or uncomfortable, they should take the headset off and rest. Check the headset maker’s age guidance for younger visitors.' ] },
    { h:'Big events', b:[
      'At a busy event, set up several stations and rotate headsets between visitors, a tip from the XR Showcase. A sign-up sheet and a timer keep the line moving fairly.',
      'Afterward, ask people what they tried and what they want next. Their answers help you pick the next playbook.' ] }
  ]},
  { id:'xr-careers', subject:'careers', icon:'case', title:'XR for Careers', sub:'Try a job before you train for it', pages:[
    { h:'Step inside a job', b:[
      'Virtual reality lets people try a job before they commit to training: stand on a factory floor, look inside a dialysis machine or practice a nursing skill.',
      'In Nevada, a program called Project SANDI put that experience in libraries and community colleges across the state.' ] },
    { h:'Project SANDI', b:[
      'SANDI stands for Supporting and Advancing Nevada’s Dislocated Individuals. It began in 2020, during the economic downturn, with a $13.8 million federal grant.',
      'The program focuses on five fields: skilled trades, healthcare, information technology, advanced manufacturing and logistics. It grew to more than 1,000 headsets at over 80 locations.' ] },
    { h:'What people do in the headset', b:[
      'Visitors take VR field trips to job sites and practice in training simulations for jobs such as dialysis technician, certified nursing assistant and HVAC technician.',
      'A nursing program coordinator at Great Basin College said the headsets allow “personal viewing and repetition of anatomy and pathophysiology.” That kind of repetition is hard to get with real equipment.' ] },
    { h:'Why libraries', b:[
      'Libraries are free, open to everyone and close to home, even in small towns. That makes them a natural place for career exploration.',
      'XRLibraries and its partner Lifeliqe installed VR headsets in Nevada community college and public libraries. XRLibraries’ homepage counts more than 1,100.' ] },
    { h:'A story from a small town', b:[
      'A remote 12-week dialysis technician certification let people train without traveling to a training center. In a community of about 300 people, a single mother finished the program and passed her certification.',
      'She plans to become a registered nurse. For many rural learners, the library is the closest classroom.' ] }
  ]},
  { id:'first-job', subject:'careers', icon:'case', title:'Your First Job', sub:'Finding it, getting it, keeping it', pages:[
    { h:'Where to start', b:[
      'First jobs are often in restaurants, stores, summer camps and farms, or helping neighbors with yard work and babysitting. Think about what you like to do and what you are good at.',
      'Ask family, teachers, coaches and neighbors. Many jobs are found through people you know. In many states, workers under 18 need a work permit, often issued through their school.' ] },
    { h:'Your résumé', b:[
      'A résumé is a one-page summary of you as a worker. Include your contact information, your school, any jobs or volunteer work, skills like languages, computers or tools, and activities that show responsibility.',
      'Keep it neat, short and honest, and ask someone to proofread it.' ] },
    { h:'The interview', b:[
      'Before an interview, learn about the business. Dress a little nicer than the job requires and arrive five to ten minutes early.',
      'Give specific examples. “I walked my neighbor’s dogs every day for a summer” shows reliability better than “I’m responsible.” At the end, ask a question about the job and thank the interviewer.' ] },
    { h:'On the job', b:[
      'Show up on time, put your phone away and ask questions when you are not sure. Mistakes happen to everyone. Own them and fix them.',
      'Reliability is the quality employers value most in a new worker, and it is how you earn a good reference for your next job.' ] },
    { h:'Your rights', b:[
      'You must be paid at least the minimum wage, which in many places is higher than the federal minimum. Teens have limits on how many hours they can work on school days.',
      'You have the right to a safe workplace and to speak up about unsafe conditions. If something feels wrong, talk to a trusted adult or your state’s labor office.' ] }
  ]},
  { id:'making-360', subject:'story', icon:'camera', title:'Making 360 Stories', sub:'Film a place so others can stand in it', pages:[
    { h:'What is a 360 story?', b:[
      'A 360 story is a short video or photo tour filmed in every direction, so viewers can look around as if they were there. It can show a historic site, a cultural event or how something is made from start to finish.',
      'In 2022 the Washington State Library ran a grant program that gave six libraries the equipment and training to make 360 stories about topics important to their communities. XRLibraries was the trainer.' ] },
    { h:'Plan with your community', b:[
      'Pick a story that matters locally, and partner with the people who know it best, such as a historical society, a cultural group, a tribe or a local business.',
      'Write a simple shot list: the places to film, who will speak, and what you want viewers to notice in each scene.' ] },
    { h:'Filming tips', b:[
      'Put the camera on a tripod at about eye level, around five feet high, and keep it still. A moving 360 camera can make viewers feel sick.',
      'The camera sees everything, so either step out of the scene or become part of it. Keep important things away from the seam between the lenses, and film in even light.' ] },
    { h:'Sound and story', b:[
      'Sound tells viewers where to look. Record clear narration or interviews, and capture the natural sounds of the place.',
      'Keep each scene short, often 30 to 90 seconds, and give viewers time to look around before the next scene starts.' ] },
    { h:'Sharing it', b:[
      'Stitch the footage in the camera’s app, then share it on headsets, as a 360 video online or in a virtual tour builder. The XR Showcase features Uptale, a platform for building 360 virtual tours.',
      'Save the original files, notes and permissions with your library’s collection so the story lasts.' ] }
  ]},
  { id:'oral-history', subject:'story', icon:'mic', title:'Recording an Oral History', sub:'How to save the stories of your elders', pages:[
    { h:'What is oral history?', b:[
      'An oral history is a recorded interview with someone about their own memories and experiences. It captures things no newspaper wrote down: how a place smelled, what people joked about, how it felt to live through a flood or a war.',
      'Many of the voices in Lost Stories projects, and in any library’s local history collection, start with interviews like these.' ] },
    { h:'Before the interview', b:[
      'Choose someone whose story you want to save, like a grandparent, a neighbor or an elder. Ask permission, explain why you are recording, and tell them where the recording will be kept.',
      'In many communities, including many Native nations, some stories belong to a family or to the community, so ask who has the right to share them.' ] },
    { h:'Good questions', b:[
      'Start easy: “Where did you grow up?” Ask open questions that cannot be answered with yes or no, like “What was a normal school day like?” or “Tell me about your first job.”',
      'Ask for details: “What did it look like? Who was there?” Then listen. Silence is fine. People often remember more if you wait.' ] },
    { h:'Recording tips', b:[
      'A phone works well. Find a quiet room away from fans, TVs and kitchens. Set the phone close to the speaker on something soft, and test a short clip first.',
      'At the start, say the date, the place and both of your names. Keep interviews to about an hour so no one gets too tired.' ] },
    { h:'After the interview', b:[
      'Thank the person and give them a copy. Label the file with names, the date and the place, write a short summary, and keep a backup.',
      'Ask your local library, historical society or tribal archive whether they collect oral histories. Your recording could help someone a hundred years from now.' ] }
  ]},
  { id:'lost-stories', subject:'equity', icon:'ship', title:'Lost Stories', sub:'Using XR to bring hidden history back', pages:[
    { h:'Who gets remembered?', b:[
      'History books leave people out. The stories of workers, immigrants, women and communities of color often survive only in family memories, letters and photographs.',
      'XRLibraries calls its work to recover these histories Lost Stories, using XR to bring marginalized history back into view.' ] },
    { h:'A Way Out of No Way', b:[
      'During World War II, thousands of people came to Marin County to build ships, and many African-American workers and their families lived in Marin City.',
      'Marin City students who call themselves the Marinovators built a VR experience of the shipyard and life in Marin City, with a musical tribute to the Black workers whose stories were rarely told.' ] },
    { h:'From a school bus to the Supreme Court', b:[
      'Another Lost Stories piece is an animated VR telling of Briggs v. Elliott in South Carolina, a case that grew out of Black families’ fight for a school bus for their children.',
      'Briggs v. Elliott became one of the cases decided together in Brown v. Board of Education in 1954, when the Supreme Court ruled that segregated public schools were unconstitutional.' ] },
    { h:'What comes next', b:[
      'XRLibraries plans to search for Latino, Asian-Pacific and Native American lost stories.',
      'Any community can start. Collect oral histories, scan family photos and documents, and ask elders what the official history left out.' ] },
    { h:'Doing it right', b:[
      'Lost stories belong to the people who lived them. Ask permission, credit storytellers if they want credit, and let the community decide how its story is told.',
      'For tribal communities, that can mean keeping some knowledge private. Good projects plan for what should not be shared as carefully as for what should.' ] }
  ]},
  { id:'reading-past', subject:'equity', icon:'lens', title:'Reading the Past', sub:'How to use primary sources', pages:[
    { h:'What is a primary source?', b:[
      'A primary source is something made at the time you are studying, by people who were there: a newspaper, a photograph, a letter, a map, a diary or a recorded interview.',
      'A secondary source is made later by someone looking back, like a textbook or a documentary. Primary sources let you meet the past up close. Secondary sources help you see the bigger story around them.' ] },
    { h:'Five questions to ask', b:[
      { li:['Who made this?', 'When and where was it made?', 'Why was it made, and who was it for?', 'What does it show or say?', 'What does it leave out?'] },
      'These questions are not about deciding a source is good or bad. They help you understand what each source can and cannot tell you.' ] },
    { h:'Look closely', b:[
      'Slow down and describe before you decide. In a photograph, look at clothing, signs, tools and the weather. In a newspaper, read the ads as well as the headlines.',
      'Notice the words people used. Some words from the past are now known to be hurtful. Historians study them carefully without repeating them casually.' ] },
    { h:'Compare sources', b:[
      'One source is a clue. Several sources together start to make a case. If a newspaper says a crowd met the first train, does a photograph or a diary agree?',
      'When sources disagree, ask why. Each person saw the event from a different place, with different reasons for remembering it.' ] },
    { h:'Find your own', b:[
      'Many libraries keep local newspapers, photographs and maps. The Library of Congress runs a free website called Chronicling America with millions of digitized newspaper pages.',
      'Your family is an archive too. Old photos, letters, recipes and the stories your elders tell are primary sources for the history of your town.' ] }
  ]},
  { id:'oceans-vr', subject:'environment', icon:'wave', title:'Oceans in VR', sub:'Reefs, bleaching and acid seas', pages:[
    { h:'Visit the reef', b:[
      'Most people will never dive a coral reef, but a headset can take them there. Hydrous, a partner listed by XRLibraries, makes VR experiences of the coral reefs of Palau, with turtles, manta rays and sharks.',
      'Its experiences come with lesson plans and activities, so a visit can turn into a science class.' ] },
    { h:'Coral bleaching', b:[
      'Corals get much of their food and their color from tiny algae living in their tissues. When the water stays too warm for too long, corals push the algae out and turn white. This is coral bleaching.',
      'Bleached corals are not dead yet, but they are starving. If the water cools in time, the algae can return.' ] },
    { h:'Ocean acidification', b:[
      'The ocean absorbs a large share of the carbon dioxide people release into the air, roughly a quarter of it. That carbon dioxide makes seawater more acidic.',
      'More acidic water makes it harder for corals, clams, oysters and some plankton to build shells and skeletons. The Stanford Ocean Experience, one of XRLibraries’ environment projects, is a VR experience about this problem.' ] },
    { h:'Talk about it', b:[
      'XRLibraries’ Climate Change Playbook gathers VR apps about climate change for viewing and discussion. The discussion is the important part.',
      'After a VR visit, ask: What surprised you? What would you want to see again? What could our town do?' ] },
    { h:'From the ocean to your sink', b:[
      'The water in the ocean is connected to the water in your sink through the water cycle. What happens to rivers and rain eventually reaches the sea.',
      'The Water Cycle, on the same shelf, follows a drop of water around the planet.' ] }
  ]},
  { id:'water-cycle', subject:'environment', icon:'drop', title:'The Water Cycle', sub:'Where every drop has been', pages:[
    { h:'Water on the move', b:[
      'The water you drink today may once have been part of an ocean, a cloud or a glacier. Earth’s water moves in a loop called the water cycle, powered by energy from the sun.',
      'About 97 percent of Earth’s water is salty ocean water. Less than 3 percent is fresh, and most of that is frozen in ice sheets and glaciers.' ] },
    { h:'Evaporation and transpiration', b:[
      'Heat from the sun turns liquid water into an invisible gas called water vapor. This is evaporation.',
      'Plants add water vapor too. They pull water up from the soil and release it through tiny pores in their leaves, a process called transpiration.' ] },
    { h:'Condensation', b:[
      'As moist air rises, it cools. Cooler air cannot hold as much water vapor, so the vapor condenses into tiny droplets that form clouds.',
      'You can see condensation when a cold glass “sweats” on a hot day.' ] },
    { h:'Precipitation and collection', b:[
      'When cloud droplets join into drops heavy enough to fall, we get precipitation: rain, snow, sleet or hail.',
      'Water collects in oceans, lakes and rivers, soaks into the ground to become groundwater, or is stored as snow and ice. Then the cycle starts again.' ] },
    { h:'California’s water', b:[
      'In California, much of the year’s water falls as winter snow in the Sierra Nevada. The snowpack works like a frozen reservoir, melting slowly through spring and summer.',
      'In dry years there is less snowpack, and in very wet years rivers can flood. Droughts and floods are part of the same cycle.' ] }
  ]},
  { id:'worlds-browser', subject:'worlds', icon:'globe', title:'Worlds in the Browser', sub:'Shared 3D spaces anyone can open', pages:[
    { h:'A world anyone can open', b:[
      'Some virtual worlds need a headset or a gaming computer. Others run in a web browser, so anyone with a phone, laptop or library computer can visit.',
      'XRLibraries builds several shared worlds on FrameVR, a browser-based platform it describes as accessible across all devices.' ] },
    { h:'Freedom to Read', b:[
      'Freedom to Read is a VR environment built with the SJSU School of Information, Unite Against Book Bans, Little Free Library and Books Unbanned.',
      'It helps citizens, librarians and students fight book bans, and helps young people in affected areas find challenged books that reflect their lives.' ] },
    { h:'Children Draw War, Not Flowers', b:[
      'This immersive 3D exhibition shares art by children in Ukraine’s Cherkasy region, which took in more than 42,000 displaced children after the Russian invasion.',
      'Librarians from 40 regional libraries, veterans and SJSU iSchool faculty and students took part. Funds bought a scanner so libraries could digitize the children’s artwork, and the project was honored at the Anthem Awards.' ] },
    { h:'Seeking Immortality', b:[
      'Built with the Northern Cheyenne Tribe and funded by an IMLS Native American Enhancement Grant, this browser-based world preserves endangered Cheyenne language and cultural knowledge.',
      'Tribal members and students were trained in 3D scanning and other tools to build and manage the space, so the tribe keeps control of its own data.' ] },
    { h:'Plan your own world', b:[
      'Start with who it is for and what it should do. Decide what belongs in public, what should stay private, and who gets to make that call.',
      'Make it simple to enter, label everything clearly and test it on a phone. A world only works if people can find their way around.' ] }
  ]},
  { id:'code', subject:'tech', icon:'code', title:'How Computers Follow Instructions', sub:'A first look at code', pages:[
    { h:'Instructions all the way down', b:[
      'A computer does not think the way you do. It follows instructions very fast and exactly as written.',
      'A list of step-by-step instructions that solves a problem is called an algorithm. A recipe is an algorithm for cooking. A program is an algorithm written in a language a computer can run.' ] },
    { h:'Bits and bytes', b:[
      'Inside, computers store everything as bits, which are 1s and 0s. Eight bits make a byte, which can stand for a number from 0 to 255, a letter, or part of a color or a sound.',
      'The letter A, for example, is stored as the number 65, which in binary is 01000001.' ] },
    { h:'Building blocks', b:[
      { li:['Variables are named boxes that hold values, like score = 0.', 'Conditionals make choices: if the score is more than 10, show “You win!”', 'Loops repeat steps: for each student in the class, print their name.', 'Functions bundle steps into a named action you can reuse.'] },
      'Almost every program, from a calculator to a VR game, is built from these few ideas.' ] },
    { h:'A tiny program', b:[
      { code:'total = 0\nfor each number from 1 to 5:\n    total = total + number\nshow total' },
      'This program adds 1 + 2 + 3 + 4 + 5 and shows 15. Change the 5 to 100 and the computer adds the numbers from 1 to 100 just as easily. The answer is 5,050.' ] },
    { h:'Bugs', b:[
      'A mistake in a program is called a bug. In 1947, engineers working on the Harvard Mark II computer found a real moth stuck in a relay and taped it into their logbook as the “first actual case of bug being found.”',
      'Every programmer writes bugs. Good programmers test their code, read error messages carefully and fix one thing at a time.' ] }
  ]},
  { id:'ai', subject:'tech', icon:'network', title:'How AI Works', sub:'And when to double-check it', pages:[
    { h:'What is AI?', b:[
      'Artificial intelligence, or AI, is software that learns patterns from examples instead of following only hand-written rules.',
      'A spam filter learns from millions of emails which ones are junk. A photo app learns what faces look like. A chat assistant learns patterns of language from huge amounts of text.' ] },
    { h:'How a language model writes', b:[
      'A language model writes a little bit of text at a time, choosing what is likely to come next based on the patterns it learned. That is why it can write smooth sentences on almost any topic.',
      'It is also why it can state something false in a confident voice. People call these mistakes hallucinations.' ] },
    { h:'Using AI well', b:[
      'Treat AI like a helpful but imperfect study partner. Ask it to explain ideas in different ways, quiz you or give feedback on your writing.',
      'Check important facts against trusted sources. If you use AI for schoolwork, follow your teacher’s rules and be honest about how you used it.' ] },
    { h:'Privacy and safety', b:[
      'Do not share private information like your address, passwords or photos of other people with AI tools or websites you do not trust.',
      'Images, videos and voices can be made by AI, so a shocking clip online may not be real. Look for the original source before you believe it or share it.' ] },
    { h:'The staff on this campus', b:[
      'Margaret, Rosa, Mr. Hale and Coach Rae are virtual staff. They answer common questions from what they know about this campus, and when AI is available they can answer more.',
      'They are not real people. A real library would decide what its own guides know and how they speak.' ] }
  ]}
];
const BOOK = {}; BOOKS.forEach((b) => BOOK[b.id] = b);
function blockText(b){ if (typeof b === 'string') return b; if (b.li) return b.li.join(' '); if (b.q) return b.q; if (b.note) return b.note; return ''; }
function srcList(keys){ return (keys || []).map((k) => SOURCES[k]).filter(Boolean); }
