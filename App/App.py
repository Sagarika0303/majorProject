# ✅ FINAL PATCHED APP.PY (Complete with Admin Pie Charts + LinkedIn Field Prediction + Bonus Videos)

import streamlit as st
import nltk
import spacy
import PyPDF2
import time
nltk.download('stopwords')
spacy.load('en_core_web_sm')

import pandas as pd
import base64, random
import matplotlib.pyplot as plt
from pyresparser import ResumeParser
from streamlit_tags import st_tags
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
from email.mime.text import MIMEText
import smtplib
import os

connection = pymysql.connect(
    host=os.environ['DB_HOST'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME'],
    port=int(os.environ.get('DB_PORT', 25524))
)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS job_postings (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    job_title VARCHAR(100),
    company_name VARCHAR(100),
    required_skills TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS applications (
    app_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT,
    name VARCHAR(100),
    email VARCHAR(100),
    resume_skills TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    domain VARCHAR(100),
    experience_level VARCHAR(50),
    FOREIGN KEY(job_id) REFERENCES job_postings(job_id)
)""")
connection.commit()

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY"  # Replace with your SendGrid API key
FROM_EMAIL = "your_verified_email@example.com"  # Replace with your verified sender email

def send_custom_mail(name, email, status, skills):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = f"Application {status}"
    content = f"Hi {name},\n\nYour application has been {status.lower()}.\n\nSkills Found: {skills}\n\nResume Analyzer Team"
    mail = Mail(
        from_email=Email(FROM_EMAIL),
        to_emails=To(email),
        subject=subject,
        plain_text_content=Content("text/plain", content)
    )
    try:
        response = sg.send(mail)
        print(f"Email sent to {email}, status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def run():
    import pandas as pd  # Ensure pandas is imported here for local scope
    st.title("Resume Analyser and Career Recommendation System using NLP")
    role = st.sidebar.selectbox("Select Role", ["User", "Admin"])

    if role == "Admin":
        admin_pass = st.text_input("Enter Admin Password", type="password")
        if st.button("Login as Admin"):
            if admin_pass == "admin123":
                st.session_state['admin_logged_in'] = True
            else:
                st.error("❌ Invalid password!")

        if not st.session_state.get('admin_logged_in'):
            st.stop()

        st.header("Admin Panel")

        st.subheader("📄 Post New Job")
        job_title = st.text_input("Job Title")
        company_name = st.text_input("Company Name")
        required_skills = st_tags(label='Required Skills', key='skills1')
        if st.button("Post Job"):
            skills_str = ', '.join(required_skills)
            cursor.execute("INSERT INTO job_postings (job_title, company_name, required_skills) VALUES (%s, %s, %s)", (job_title, company_name, skills_str))
            connection.commit()
            st.success("✅ Job Posted!")

        st.subheader("📄 View All Jobs Posted")
        cursor.execute("SELECT job_id, job_title, company_name, required_skills FROM job_postings")
        jobs = cursor.fetchall()
        if jobs:
            # Display jobs with sequential numbering in UI
            jobs_list = []
            for idx, j in enumerate(jobs, start=1):
                jobs_list.append(f"{idx}. {j[1]} at {j[2]} (ID {j[0]})")
            selected_job_str = st.selectbox("Select Job to View Details", jobs_list)
            if st.button("Delete Selected Job"):
                job_id = jobs[int(selected_job_str.split('.')[0]) - 1][0]
                # Delete all applications for the job first
                cursor.execute("DELETE FROM applications WHERE job_id = %s", (job_id,))
                connection.commit()
                # Reset auto-increment counter for applications table
                cursor.execute("SELECT MAX(app_id) FROM applications")
                max_app_id = cursor.fetchone()[0]
                if max_app_id is None:
                    max_app_id = 0
                cursor.execute(f"ALTER TABLE applications AUTO_INCREMENT = {max_app_id + 1}")
                connection.commit()
                # Now delete the job posting
                cursor.execute("DELETE FROM job_postings WHERE job_id = %s", (job_id,))
                connection.commit()
                st.success("Job and associated applicants deleted successfully.")

            if st.button("Clear Applicants Data"):
                job_id = jobs[int(selected_job_str.split('.')[0]) - 1][0]
                cursor.execute("SELECT COUNT(*) FROM applications WHERE job_id = %s", (job_id,))
                app_count = cursor.fetchone()[0]
                if app_count == 0:
                    st.info("No applicants to clear for this job.")
                else:
                    cursor.execute("DELETE FROM applications WHERE job_id = %s", (job_id,))
                    connection.commit()
                    # Reset auto-increment counter for applications table
                    cursor.execute("SELECT MAX(app_id) FROM applications")
                    max_app_id = cursor.fetchone()[0]
                    if max_app_id is None:
                        max_app_id = 0
                    cursor.execute(f"ALTER TABLE applications AUTO_INCREMENT = {max_app_id + 1}")
                    connection.commit()
                    st.success("All applicants data cleared for the selected job.")
            selected_index = int(selected_job_str.split('.')[0]) - 1
            job = jobs[selected_index]
            job_id, job_title, company_name, required_skills_str = job
            st.write(f"### Required Skills:")
            skills_list = [skill.strip() for skill in required_skills_str.split(',')]
            st.markdown(
                ''.join([f"<span style='display:inline-block; background-color:#1ed760; color:#fff; border-radius:4px; padding:4px 8px; margin:2px;'>{skill}</span>" for skill in skills_list]),
                unsafe_allow_html=True
            )
            # Show applicants associated with selected job
            cursor.execute("SELECT app_id, name, email, resume_skills, status FROM applications WHERE job_id = %s", (job_id,))
            applicants = cursor.fetchall()
            if applicants:
                st.subheader("Applicants for this Job :")
                applicants_df = pd.DataFrame(applicants, columns=['App ID', 'Name', 'Email', 'Skills', 'Status'])
                st.dataframe(applicants_df[['Name', 'Email', 'Skills', 'Status']])
                options = [f"{row['App ID']} - {row['Name']} - {row['Email']}" for idx, row in applicants_df.iterrows()]
                selected_option = st.selectbox("Select Applicant", options)
                selected_app_id = int(selected_option.split(' - ')[0])
                if st.button("Select Applicant"):
                    selected_row = applicants_df[applicants_df['App ID'] == selected_app_id].iloc[0]
                    cursor.execute("UPDATE applications SET status = %s WHERE app_id = %s", ('Selected', selected_app_id))
                    connection.commit()
                    send_custom_mail(selected_row['Name'], selected_row['Email'], 'Selected', selected_row['Skills'])
                    st.success(f"Applicant {selected_row['Name']} selected and notified.")
                if st.button("Reject Applicant"):
                    selected_row = applicants_df[applicants_df['App ID'] == selected_app_id].iloc[0]
                    cursor.execute("UPDATE applications SET status = %s WHERE app_id = %s", ('Rejected', selected_app_id))
                    connection.commit()
                    send_custom_mail(selected_row['Name'], selected_row['Email'], 'Rejected', selected_row['Skills'])
                    st.warning(f"Applicant {selected_row['Name']} rejected and notified.")
            else:
                st.info("No applicants for this job yet.")
        else:
            st.write("No jobs posted yet.")

        cursor.execute("SELECT app_id, name, email, resume_skills, status FROM applications")
        all_apps = cursor.fetchall()
        columns = ['App ID', 'Name', 'Email', 'Skills', 'Status']
        df = pd.DataFrame(all_apps, columns=columns)

        if not df.empty:
            st.subheader("📊 Applicant Distribution Charts")
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                st.markdown("*By Status*")
                status_counts = df['Status'].value_counts()
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(4,4))
                status_counts.plot.pie(ax=ax, autopct="%.1f%%", ylabel='')
                st.pyplot(fig)

            with col2:
                st.markdown("*By Experience Level*")
                cursor.execute("SELECT experience_level FROM applications")
                exp_data = cursor.fetchall()
                exp_levels = [item[0] for item in exp_data if item[0]]
                if exp_levels:
                    exp_counts = pd.Series(exp_levels).value_counts()
                    fig3, ax3 = plt.subplots(figsize=(4,4))
                    exp_counts.plot.pie(ax=ax3, autopct="%.1f%%", ylabel='')
                    st.pyplot(fig3)
                else:
                    st.write("No experience level data available.")

            with col3:
                st.markdown("*By Branch*")
                cursor.execute("SELECT branch FROM applications")
                branch_data = cursor.fetchall()
                branch_list = [item[0] if item[0] else 'Unknown' for item in branch_data]
                if branch_list:
                    branch_counts = pd.Series(branch_list).value_counts()
                    fig4, ax4 = plt.subplots(figsize=(4,4))
                    branch_counts.plot.pie(ax=ax4, autopct="%.1f%%", ylabel='')
                    st.pyplot(fig4)
                else:
                    st.write("No branch data available.")

            
            st.subheader("📄 All Resumes Details")
            # Fetch all applications with additional info if available
            cursor.execute("SELECT name, email, resume_skills, status, experience_level, branch FROM applications")
            resumes = cursor.fetchall()
            # Create DataFrame with placeholders for missing columns
            resumes_df = pd.DataFrame(resumes, columns=['Name', 'Email', 'Skills', 'Status', 'Experience Level', 'Branch'])
            # Remove placeholder columns and fetch actual data
            cursor.execute("SELECT name, email, resume_skills, status, experience_level, branch, phone_number, missing_skills, resume_score FROM applications")
            resumes = cursor.fetchall()
            resumes_df = pd.DataFrame(resumes, columns=['Name', 'Email', 'Skills', 'Status', 'Experience Level', 'Branch', 'Phone Number', 'Missing Skills', 'Resume Score'])
            # Update Predicted Field column with domain from database
            cursor.execute("SELECT domain FROM applications")
            domains = cursor.fetchall()
            domain_list = [d[0] if d[0] else 'Unknown' for d in domains]
            if len(domain_list) == len(resumes_df):
                resumes_df['Predicted Field'] = domain_list
            else:
                resumes_df['Predicted Field'] = 'Unknown'
            st.dataframe(resumes_df)


    else:
        st.header("User - Apply + Resume Analysis")
        cursor.execute("SELECT job_id, job_title, company_name, required_skills FROM job_postings")
        jobs = cursor.fetchall()

        if not jobs:
            st.warning("No Jobs Posted Yet.")
            return

        jobs_dict = {f"{j[1]} at {j[2]} (ID {j[0]})": (j[0], j[3]) for j in jobs}
        selected_job = st.selectbox("Select Job", list(jobs_dict.keys()))
        job_id, required_skills_str = jobs_dict[selected_job]
        required_skills = [s.strip().lower() for s in required_skills_str.split(',')]
        st.write(f"### Required Skills: {', '.join(required_skills)}")

        pdf_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            os.makedirs("Uploaded_Resumes", exist_ok=True)
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                with open(save_image_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_pages = len(pdf_reader.pages)
                    full_text = ""
                    for page in pdf_reader.pages:
                        full_text += page.extract_text() + " "
        
                st.success("Hello " + resume_data.get('name', 'User'))
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name : ' + resume_data.get('name', 'Unknown'))
                    st.text('Email : ' + resume_data.get('email', 'Unknown'))
                    st.text('Contact : ' + resume_data.get('mobile_number', 'Unknown'))
                    st.text('Resume pages : ' + str(num_pages))
                except Exception:
                    pass

                resume_skills = [s.lower() for s in resume_data.get('skills', [])]
                missing_skills = list(set(required_skills) - set(resume_skills))
                st.subheader("**Skill Recommendation**")
                if missing_skills:
                    st.markdown("**Missing Skills :**")
                    st.markdown(
                        ''.join([f"<span style='display:inline-block; background-color:#fabc10; color:#333; border-radius:4px; padding:4px 8px; margin:2px;'>{skill}</span>" for skill in missing_skills]),
                        unsafe_allow_html=True
                    )
                else:
                    st.success("You match all skills!")

                st.markdown("**Skills you have :**")
                skills_list_user = [skill.strip() for skill in resume_data.get('skills', [])]
                st.markdown(
                    ''.join([f"<span style='display:inline-block; background-color:#1ed760; color:#fff; border-radius:4px; padding:4px 8px; margin:2px;'>{skill}</span>" for skill in skills_list_user]),
                    unsafe_allow_html=True
                )

                reco_field = 'Unknown'
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'php', 'laravel', 'magento', 'wordpress', 'javascript']
                android_keyword = ['android', 'flutter', 'kotlin']
                ios_keyword = ['ios', 'swift', 'xcode']
                uiux_keyword = ['ux', 'figma', 'adobe xd']

                resume_text = ', '.join(resume_skills)

                if any(i in resume_text for i in ds_keyword):
                    reco_field = 'Data Science'
                    course_recommend(ds_course, resume_data)
                elif any(i in resume_text for i in web_keyword):
                    reco_field = 'Web Development'
                    course_recommend(web_course, resume_data)
                elif any(i in resume_text for i in android_keyword):
                    reco_field = 'Android Development'
                    course_recommend(android_course, resume_data)
                elif any(i in resume_text for i in ios_keyword):
                    reco_field = 'IOS Development'
                    course_recommend(ios_course, resume_data)
                elif any(i in resume_text for i in uiux_keyword):
                    reco_field = 'UI-UX Development'
                    course_recommend(uiux_course, resume_data)

                if reco_field != 'Unknown':
                    link = f"https://www.linkedin.com/jobs/search/?keywords={reco_field.replace(' ', '%20')}"
                    st.markdown(f"[🔗 Find {reco_field} Jobs on LinkedIn]({link})", unsafe_allow_html=True)

                # Display recommended field explicitly
                st.subheader("**Recommended Field:**")
                st.success(f"### {reco_field}")


                # Add LinkedIn job search based on recommended skills
                def generate_linkedin_url(recommended_skills):
                    skills_query = '+'.join([skill.replace(' ', '+') for skill in recommended_skills])
                    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={skills_query}"
                    return linkedin_url

                if resume_skills:
                    st.subheader("**Job Opportunities Based on Your Skills 💼**")
                    linkedin_url = generate_linkedin_url(resume_skills)
                    st.success("** Our analysis recommends you the following jobs based on the skills mentioned in your resume**")
                    cand_level = ''
                    if num_pages == 1:
                        cand_level = "Fresher"
                        st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',
                                    unsafe_allow_html=True)
                    elif num_pages == 2:
                        cand_level = "Intermediate"
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                    unsafe_allow_html=True)
                    elif num_pages >= 3:
                        cand_level = "Experienced"
                        st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!</h4>''',
                                    unsafe_allow_html=True)
                    if st.button("Find recommended jobs on LinkedIn"):
                        import webbrowser
                        webbrowser.open(linkedin_url)

                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                st.subheader("📊 Resume Score**")
                resume_score = 0
                resume_text = full_text.lower()

                # Define keyword groups
                keyword_groups = {
                    "Projects": ["project", "projects", "academic project", "academic projects"],
                    "Internships": ["internship", "internships","intern", "interns"],
                    "Work Experience": ["job", "jobs", "work experience", "experience", "roles", "work", "employment", "employments", "company", "companies", "organization", "organizations", "org", "orgs", "work history", "work history", "roles and responsibility", "roles & responsibility", "responsibility", "responsibilities", "position of responsibility", "position of responsibilities", "positions of responsibilities"],
                    "Awards and Achievements": ["award", "awards", "honour", "honours", "achievement", "achievements", "certification", "certifications", "extra-curricular activities", "activity", "activities"]
                }

                points_per_group = 25  # Distribute 100 points equally among 4 groups

                for group_name, keywords in keyword_groups.items():
                    if any(keyword in resume_text for keyword in keywords):
                        resume_score += points_per_group
                        st.markdown(
                            f'''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added {group_name}</h4>''',
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add {group_name} to strengthen your resume.</h4>''',
                            unsafe_allow_html=True)
                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()

                if st.button("Apply Now"):
                    # Determine experience level based on number of pages
                    experience_level = ''
                    if num_pages == 1:
                        experience_level = "Fresher"
                    elif num_pages == 2:
                        experience_level = "Intermediate"
                    elif num_pages >= 3:
                        experience_level = "Experienced"

                    # Determine domain from reco_field
                    domain = reco_field if reco_field != 'Unknown' else ''

                    # Extract branch from resume text or skills
                    def extract_branch(text, skills):
                        branches = ['computer science', 'electronics', 'mechanical', 'civil', 'electrical', 'information technology', 'it', 'chemical', 'biotechnology', 'aerospace', 'industrial', 'environmental', 'software', 'data science']
                        text_lower = text.lower()
                        skills_lower = [s.lower() for s in skills]
                        for branch in branches:
                            if branch in text_lower or branch in skills_lower:
                                return branch.title()
                        return 'Unknown'

                    branch = extract_branch(full_text, resume_skills)

                    # Calculate missing skills string
                    missing_skills_str = ', '.join(missing_skills) if missing_skills else ''
                    # Insert with new columns phone_number, missing_skills, resume_score
                    cursor.execute("INSERT INTO applications (job_id, name, email, resume_skills, experience_level, domain, branch, phone_number, missing_skills, resume_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                   (job_id, resume_data.get('name', 'Unknown'), resume_data.get('email', 'Unknown'), ', '.join(resume_skills), experience_level, domain, branch, resume_data.get('mobile_number', 'Unknown'), missing_skills_str, resume_score))
                    connection.commit()
                    st.success("✅ Application Submitted!")

                name = resume_data.get('name', 'Unknown')
                email = resume_data.get('email', 'Unknown')
                send_resume_email(name, email, resume_score, keywords, missing_skills, reco_field)

def course_recommend(course_list, resume_data):
    st.subheader("*Courses & Certificates🎓 Recommendations*")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

def course_recommender(course_list):
    c = 0
    no_of_reco = st.slider('No. of Videos', 1, 10, 2)
    random.shuffle(course_list)
    for item in course_list:
        c += 1
        if isinstance(item, (list, tuple)) and len(item) == 2:
            c_name, c_link = item
            st.markdown(f"({c}) [{c_name}]({c_link})")
        elif isinstance(item, str):
            st.markdown(f"({c}) [Video Link]({item})")
        else:
            st.markdown(f"({c}) {item}")
        if c == no_of_reco:
            break

def send_resume_email(name, email, resume_score, skills, reco_skills, reco_courses):
    body = f"""
Hi {name},

Your Resume Review:
Resume Score: {resume_score}
Skills: {skills}
Missing Skills: {reco_skills}
Recommended Field: {reco_courses}

Improve and Apply on LinkedIn!
"""
    msg = MIMEText(body)
    msg['Subject'] = 'Your Resume Review Summary'
    msg['From'] = '245621737117.glwec@gmail.com'
    msg['To'] = email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login("245621737117.glwec@gmail.com", "Domino@123")
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(e)

run()
