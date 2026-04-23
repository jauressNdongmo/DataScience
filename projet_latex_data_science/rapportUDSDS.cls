\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{rapportUDSDS}[2026/04/01 Classe de rapport UDS pour Science des Donnees]
\LoadClass[a4paper,12pt,oneside]{report}

% ---------------- Packages de base ----------------
\RequirePackage[french]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{mathptmx}
\RequirePackage[left=2.6cm,right=2.6cm,top=2.5cm,bottom=2.8cm]{geometry}
\RequirePackage{graphicx}
\RequirePackage{array}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\RequirePackage{longtable}
\RequirePackage{multirow}
\RequirePackage{enumitem}
\RequirePackage{setspace}
\RequirePackage{xcolor}
\RequirePackage{titlesec}
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
\RequirePackage{hyperref}
\RequirePackage{wallpaper}
\RequirePackage{caption}
\RequirePackage{float}
\RequirePackage{amsmath,amssymb}
\RequirePackage{tocloft}
\RequirePackage{etoolbox}
\RequirePackage{ifthen}
\RequirePackage{colortbl}
\RequirePackage{ragged2e}
\RequirePackage{eso-pic}
\hypersetup{hidelinks,pdfauthor={},pdftitle={Rapport de Science des Donnees}}

% ---------------- Identite visuelle ----------------
\definecolor{UDSBlue}{HTML}{123B6D}
\definecolor{UDSDark}{HTML}{1E2A38}
\definecolor{UDSGold}{HTML}{D98B1F}
\definecolor{UDSLight}{HTML}{F4F7FB}
\definecolor{UDSGray}{HTML}{6B7280}
\definecolor{TableHeader}{HTML}{E8EEF7}
\definecolor{TableAlt}{HTML}{F8FAFD}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.45em}
\setlength{\headheight}{25pt}
\onehalfspacing

% ---------------- Informations du rapport ----------------
\newcommand{\module}[1]{\gdef\@module{#1}}
\newcommand{\theme}[1]{\gdef\@theme{#1}}
\newcommand{\titre}[1]{\gdef\@titre{#1}}
\newcommand{\professeur}[1]{\gdef\@professeur{#1}}
\newcommand{\anneeacademique}[1]{\gdef\@anneeacademique{#1}}
\newcommand{\niveau}[1]{\gdef\@niveau{#1}}
\newcommand{\filiere}[1]{\gdef\@filiere{#1}}
\newcommand{\departement}[1]{\gdef\@departement{#1}}
\newcommand{\universite}[1]{\gdef\@universite{#1}}
\newcommand{\faculte}[1]{\gdef\@faculte{#1}}
\newcommand{\membresgroupe}[1]{\gdef\@membresgroupe{#1}}

\module{Science des Données}
\theme{}
\titre{Rapport de Science des Données}
\professeur{}
\anneeacademique{2025--2026}
\niveau{Master}
\filiere{Informatique}
\departement{Département d'Informatique}
\universite{Université de Dschang}
\faculte{Faculté des Sciences}
\membresgroupe{}

% ---------------- Style des titres ----------------
\titleformat{\chapter}[display]
  {\normalfont\bfseries\color{UDSBlue}}
  {\filleft\Large\chaptertitlename\ \thechapter}
  {0.5ex}
  {\titlerule[1pt]\vspace{1ex}\filright\Huge}
  [\vspace{1ex}\titlerule]

\titleformat{\section}
  {\normalfont\Large\bfseries\color{UDSDark}}
  {\thesection}{0.8em}{}

\titleformat{\subsection}
  {\normalfont\large\bfseries\color{UDSBlue}}
  {\thesubsection}{0.8em}{}

\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries\color{UDSGold}}
  {\thesubsubsection}{0.8em}{}

% ---------------- Entete/Pied de page ----------------
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\textcolor{UDSBlue}{\small \@universite}}
\fancyhead[R]{\textcolor{UDSGray}{\small \@module}}
\fancyfoot[L]{\textcolor{UDSGray}{\small Rapport académique}}
\fancyfoot[C]{\textcolor{UDSBlue}{\small \thepage/\pageref{LastPage}}}
\fancyfoot[R]{\textcolor{UDSGray}{\small \@anneeacademique}}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\footrulewidth}{0.5pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{UDSBlue}\leaders\hrule height \headrulewidth\hfill}}
\renewcommand{\footrule}{\hbox to\headwidth{\color{UDSGold}\leaders\hrule height \footrulewidth\hfill}}

% ---------------- TOC ----------------
\renewcommand{\cftchapfont}{\bfseries\color{UDSBlue}}
\renewcommand{\cftchappagefont}{\bfseries\color{UDSBlue}}
\renewcommand{\cftsecfont}{\color{UDSDark}}
\renewcommand{\cftsecpagefont}{\color{UDSDark}}
\setlength{\cftbeforechapskip}{0.5em}

% ---------------- Page de garde ----------------
\newcommand{\fairepagedegarde}{%
\begin{titlepage}
\ThisCenterWallPaper{1}{logos/background.png}
\centering
\color{black}
\vspace*{-0.8cm}
\includegraphics[width=0.95\textwidth]{logos/titre_logo_uds.png}\par

\vspace{2.9cm}
\begin{minipage}{0.82\textwidth}
\centering
{\Large\scshape \@theme\par}
\end{minipage}

\vspace{0.9cm}
\noindent\rule{0.82\textwidth}{0.6pt}\par
\vspace{0.35cm}
{\fontsize{22}{26}\selectfont\bfseries \@titre\par}
\vspace{0.35cm}
\noindent\rule{0.82\textwidth}{0.6pt}\par

\vfill

{\Large\bfseries Supervisé par :\par}
\vspace{0.15cm}
{\large \@professeur\par}

\vfill
{\large Année Universitaire \@anneeacademique\par}
\end{titlepage}
}

% ---------------- Page membres ----------------
\newcommand{\pagecompositiongroupe}[1]{%
\clearpage
\thispagestyle{plain}
\begin{center}
    {\Large\bfseries\color{UDSBlue} Composition du groupe}\par
    \vspace{0.25cm}
    {\normalsize\color{UDSGray} Matricules et noms \& prénoms des membres}\par
\end{center}
\vspace{0.6cm}
\rowcolors{2}{TableAlt}{white}
\renewcommand{\arraystretch}{1.35}
\begin{tabularx}{\textwidth}{>{\bfseries\raggedright\arraybackslash}p{4.1cm} >{\RaggedRight\arraybackslash}X}
\rowcolor{TableHeader}
\textcolor{UDSBlue}{Matricule} & \textcolor{UDSBlue}{Noms \& prénoms}\\
#1
\end{tabularx}
\clearpage
}

% ---------------- Environnements utiles ----------------
\newcommand{\encadreobjectif}[1]{%
\begin{center}
\fcolorbox{UDSBlue}{UDSLight}{\begin{minipage}{0.93\textwidth}
\textbf{Objectif du chapitre}\par #1
\end{minipage}}
\end{center}}

\newcommand{\motcle}[1]{\textcolor{UDSBlue}{\textbf{#1}}}
