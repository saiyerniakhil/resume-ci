from operator import itemgetter

import requests
from typing import Dict, Any, List, Optional
from pylatex import Document, NoEscape


def fetch(url: str) -> Dict[str, Any]:
    """Make HTTP request and return parsed response as dict."""
    try:
        print(f"fetching data from {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Request timed out: {url}")
        return {}
    except requests.exceptions.ConnectionError:
        print(f"Connection error: {url}")
        return {}
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {url}")
        return {}
    except requests.exceptions.JSONDecodeError:
        print(f"Invalid JSON response: {url}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}


class Resume:
    doc: Optional[Document] = None
    data: Dict[str, Any] = {}

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        # Document setup with custom geometry and packages
        geometry_options = {
            "left": "0.75in",
            "right": "0.75in",
            "top": "0.5in",
            "bottom": "0.75in"
        }
        self.doc = Document(geometry_options=geometry_options)

        # Add required packages
        self.doc.packages.append(NoEscape(r'\usepackage{enumitem}'))
        self.doc.packages.append(NoEscape(r'\usepackage{hyperref}'))
        self.doc.packages.append(NoEscape(r'\usepackage{amsmath}'))
        self.doc.packages.append(NoEscape(r'\usepackage[svgnames]{xcolor}'))
        self.doc.packages.append(NoEscape(r'\usepackage{sectsty}'))

        # Add color definitions and settings
        self.doc.preamble.append(NoEscape(r'\definecolor{LinkBlue}{RGB}{48,92,199}'))
        self.doc.preamble.append(NoEscape(r'\definecolor{MainBlue}{RGB}{16,82,197}'))
        self.doc.preamble.append(NoEscape(r'\hypersetup{colorlinks = true, urlcolor=LinkBlue}'))
        self.doc.preamble.append(NoEscape(r'\sectionfont{\color{MainBlue}}'))
        self.doc.preamble.append(NoEscape(r'\linespread{0.90}'))
        self.doc.preamble.append(NoEscape(r'\pagestyle{empty}'))

        # Use provided data or fetch from API
        if data:
            self.data = data
        else:
            # fetch data from API
            data = fetch("https://saiyerniakhil.in/api/data.json")
            personal_info, social_links, work_ex, skills = itemgetter('personalInfo', 'socialLinks','workExperience', 'skills')(data)
            self.data = {
                'workEx': work_ex if work_ex else [],
                'socialLinks': social_links if social_links else {},
                'personalInfo': personal_info if personal_info else {},
                'skills': skills if skills else {}
            }

    def createHeader(self) -> None:
        """Create header with name and social links"""
        # Name
        self.doc.append(NoEscape(r'\begin{center}'))
        self.doc.append(NoEscape(r'\textbf{\Huge Sai Yerni Akhil Madabattula}'))
        self.doc.append(NoEscape(r'\end{center}'))
        self.doc.append(NoEscape(r'\vspace{2mm}'))

        # Social links
        social = self.data.get('socialLinks', {})
        links = []

        if 'linkedin' in social:
            links.append(f"\\href{{{social['linkedin']}}}{{LinkedIn}}")
        if 'github' in social:
            links.append(f"\\href{{{social['github']}}}{{GitHub}}")
        if 'website' in social:
            links.append(f"\\href{{{social['website']}}}{{saiyerniakhil.in}}")
        if 'email' in social:
            links.append(f"\\href{{mailto://{social['email']}}}{{{social['email']}}}")
        if 'phone' in social:
            links.append(social['phone'])

        if links:
            self.doc.append(NoEscape(r'\begin{center}'))
            self.doc.append(NoEscape('\n\\text{\\textbar}\n'.join(links)))
            self.doc.append(NoEscape(r'\end{center}'))

    def createWorkExSection(self) -> None:
        """Create work experience section with all jobs"""
        # Section header
        self.doc.append(NoEscape(r'\section*{Work Experience}'))
        self.doc.append(NoEscape(r'{\color{MainBlue}\hrule height 0.5mm}'))
        self.doc.append(NoEscape(r'\vspace{3mm}'))

        # Get work experience from self.data and ensure it's a list
        work_ex = self.data.get('workEx', [])
        if isinstance(work_ex, dict):
            work_ex = [work_ex]

        for idx, job in enumerate(work_ex):
            # Job header - get values with defaults
            role = job.get('role', '')
            period = job.get('period', '')
            company = job.get('company', '')
            location = job.get('location', '')

            self.doc.append(NoEscape(r'\noindent'))
            self.doc.append(NoEscape(f'\\textbf{{{role}}} \\hfill {period} \\\\'))
            self.doc.append(NoEscape(f'\\text{{{company}}} \\hfill {location}'))

            # Description bullets
            descriptions = job.get('description', [])
            if descriptions:
                self.doc.append(NoEscape(r'\begin{itemize}[leftmargin=*]'))
                self.doc.append(NoEscape(r'\setlength{\itemsep}{0.02em}'))
                for desc in descriptions:
                    self.doc.append(NoEscape(f'\\item {desc}'))
                self.doc.append(NoEscape(r'\end{itemize}'))

            # Add spacing between jobs (except for last one)
            if idx < len(work_ex) - 1:
                self.doc.append(NoEscape(r'\vspace{2mm}'))

    def createSkills(self) -> None:
        """Create Skills Section"""
        # Section header
        self.doc.append(NoEscape(r'\section*{Skills}'))
        self.doc.append(NoEscape(r'{\color{MainBlue}\hrule height 0.5mm}'))
        self.doc.append(NoEscape(r'\vspace{3mm}'))

        # Get skills from self.data
        skills = self.data.get('skills', [])

        if skills:
            self.doc.append(NoEscape(r'\begin{itemize}[leftmargin=*]'))
            self.doc.append(NoEscape(r'\setlength{\itemsep}{0.02em}'))

            for skill in skills:
                skill_type = skill.get('type', '')
                values = skill.get('values', [])

                if skill_type and values:
                    # Join values with comma and space
                    values_str = ', '.join(values)
                    self.doc.append(NoEscape(f'\\item \\textbf{{{skill_type}:}} {values_str}'))

            self.doc.append(NoEscape(r'\end{itemize}'))

    def createEducation(self) -> None:
        """Create Education Section"""
        # Section header
        self.doc.append(NoEscape(r'\section*{Education}'))
        self.doc.append(NoEscape(r'{\color{MainBlue}\hrule height 0.5mm}'))
        self.doc.append(NoEscape(r'\vspace{3mm}'))

        # University of Wisconsin
        self.doc.append(NoEscape(r'\noindent'))
        self.doc.append(NoEscape(r'\textbf{University of Wisconsin,} United States \hfill Jan 2023 - Aug 2024\\'))
        self.doc.append(NoEscape(r'M.S. Computer Science \hfill GPA: 3.8\\'))
        self.doc.append(NoEscape(r'Relevant Courses: Machine Learning, Network Security, Programming Language Concepts, Concurrent Programming, Natural Language Processing, Web Development'))
        self.doc.append(NoEscape(r'\vspace{3mm}'))

        # Sathyabama Institute
        self.doc.append(NoEscape(r'\noindent'))
        self.doc.append(NoEscape(r'\textbf{Sathyabama Institute of Science and Technology,} Chennai, India \hfill July 2016 - May 2020 \\'))
        self.doc.append(NoEscape(r'B.E. Computer Science and Engineering \hfill GPA: 8.45\\'))
        self.doc.append(NoEscape(r'Courses: Data Structures, Advanced Data Structures, Machine Learning, DBMS, Operating Systems, Responsive Web Design'))

    def create(self, output_filename: str = "resume") -> str:
        """Generate the PDF resume"""
        # Create header
        self.createHeader()

        # Create work experience section
        if 'workEx' in self.data and self.data['workEx']:
            self.createWorkExSection()

        # Create skills section
        if 'skills' in self.data and self.data['skills']:
            self.createSkills()

        # Create education section
        self.createEducation()

        # Generate PDF
        self.doc.generate_pdf(output_filename, clean_tex=False)
        return f"{output_filename}.pdf"


if __name__ == "__main__":
    # Test with sample data
    sample_data = {
        'socialLinks': {
            'linkedin': 'https://www.linkedin.com/in/sai-yerni-akhil-madabattula/',
            'github': 'https://github.com/saiyerniakhil',
            'website': 'http://saiyerniakhil.in/',
            'email': 'akhilsai831@gmail.com',
            'phone': '+1 414-338-5364'
        },
        'workEx': [
            {
                "role": "Software Developer",
                "company": "GEICO Insurance",
                "location": "Seattle, WA",
                "period": "Jan, 2025 - Present",
                "description": [
                    "Contributed key features to the Internal Developer Platform using \\textbf{Go}, \\textbf{GraphQL}, and \\textbf{React}, enabling seamless team transitions and improving developer onboarding efficiency.",
                    "Developed and deployed a cross-platform CLI tool for creating WSL and Docker-based workspaces to \\textbf{5,600} developers across GEICO, standardizing development environments."
                ]
            }
        ],
        'skills': [
            {
                "type": "Languages",
                "values": ["JavaScript", "TypeScript", "HTML", "CSS", "Python", "Java", "PHP", "Scala"]
            },
            {
                "type": "Frontend",
                "values": ["React.js", "Next.JS", "Redux", "Material UI", "TailwindCSS", "Astro.js", "Webpack", "Jest"]
            },
            {
                "type": "Backend Technologies",
                "values": ["Node.js", "REST API", "MongoDB", "Postgres", "SQLite", "Flask", "Docker", "Kubernetes"]
            },
            {
                "type": "Tools",
                "values": ["Visual Studio Code", "Git", "Chrome Developer Tools", "Postman", "Figma", "Jira", "Microsoft Office Suite", "WordPress", "GitHub", "Agile (Scrum) Methodologies"]
            }
        ]
    }

    r = Resume(data=sample_data)
    r.create()