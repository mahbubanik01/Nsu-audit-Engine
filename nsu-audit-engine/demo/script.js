/**
 * NSU Graduation Audit Engine - Web Demo Logic
 * Ported from Python source code
 */

// ==========================================
// 1. Models
// ==========================================

const NSUGradeSystem = {
    points: {
        'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D+': 1.3, 'D': 1.0,
        'F': 0.0
    },

    getPoint(grade) {
        return this.points[grade] !== undefined ? this.points[grade] : 0.0;
    },

    isPassing(grade) {
        return this.points[grade] !== undefined && this.points[grade] >= 1.0;
    },

    countsInGPA(grade) {
        return ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F'].includes(grade);
    },

    getClassStanding(cgpa) {
        if (cgpa >= 3.00) return "First Class";
        if (cgpa >= 2.50) return "Second Class";
        if (cgpa >= 2.00) return "Third Class";
        return "Probation";
    }
};

class CourseRecord {
    constructor(code, credits, grade, semester) {
        this.code = code.toUpperCase().trim();
        this.credits = parseFloat(credits) || 0;
        this.grade = grade.toUpperCase().trim();
        this.semester = semester.trim();
        this.qualityPoints = NSUGradeSystem.getPoint(this.grade) * this.credits;
    }
}

class Transcript {
    constructor() {
        this.records = [];
    }

    addRecord(record) {
        this.records.push(record);
    }

    getUniqueCourses() {
        return [...new Set(this.records.map(r => r.code))];
    }

    getCourseHistory(code) {
        return this.records.filter(r => r.code === code);
    }

    getBestAttempt(code) {
        const history = this.getCourseHistory(code);
        if (history.length === 0) return null;

        return history.reduce((best, current) => {
            const currentPoints = NSUGradeSystem.getPoint(current.grade);
            const bestPoints = NSUGradeSystem.getPoint(best.grade);
            return currentPoints >= bestPoints ? current : best;
        });
    }

    getRetakenCourses() {
        const retakes = {};
        this.getUniqueCourses().forEach(code => {
            const history = this.getCourseHistory(code);
            if (history.length > 1) {
                retakes[code] = history;
            }
        });
        return retakes;
    }
}

// ==========================================
// 2. Calculators
// ==========================================

const CreditCalculator = {
    calculate(transcript) {
        let earned = 0;
        let attempted = 0;
        const uniqueCourses = transcript.getUniqueCourses();

        uniqueCourses.forEach(code => {
            const best = transcript.getBestAttempt(code);

            // Attempted: counts if F or passing (not W, I, or 0-credit)
            if (best.credits > 0 && (best.grade === 'F' || NSUGradeSystem.isPassing(best.grade))) {
                attempted += best.credits;
            }

            // Earned: only passing
            if (best.credits > 0 && NSUGradeSystem.isPassing(best.grade)) {
                earned += best.credits;
            }
        });

        return { earned, attempted };
    }
};

const GPACalculator = {
    calculate(transcript, waivedCourses = new Set()) {
        let totalPoints = 0;
        let totalCredits = 0;
        const gradeDist = {};
        const semesterData = {};

        const uniqueCourses = transcript.getUniqueCourses();

        uniqueCourses.forEach(code => {
            if (waivedCourses.has(code)) return;

            const best = transcript.getBestAttempt(code);

            // Skip non-GPA grades or 0-credit courses
            if (!NSUGradeSystem.countsInGPA(best.grade) || best.credits === 0) return;

            totalPoints += best.qualityPoints;
            totalCredits += best.credits;

            // Grade Distribution
            gradeDist[best.grade] = (gradeDist[best.grade] || 0) + 1;

            // Semester GPA Data
            if (!semesterData[best.semester]) {
                semesterData[best.semester] = { points: 0, credits: 0 };
            }
            semesterData[best.semester].points += best.qualityPoints;
            semesterData[best.semester].credits += best.credits;
        });

        const cgpa = totalCredits > 0 ? totalPoints / totalCredits : 0.0;

        return {
            cgpa,
            totalCredits,
            gradeDist,
            semesterData, // { "Spring 2023": { points: 12, credits: 3 } }
            classStanding: NSUGradeSystem.getClassStanding(cgpa)
        };
    }
};

const AuditCalculator = {
    // Hardcoded BBA Logic for demo
    BBA_REQ: {
        credits: 126,
        cgpa: 2.0,
        mandatory: [
            "ENG102", "ENG103", "ENG105", "MAT116", "MAT120", "MAT125",
            "PHI101", "PHI104", "PHI401", "LBA247", "POL101", "ECO101",
            "ECO104", "SOC101", "ENV107", "BIO103", "PSY101", "HIS101",
            "ACT201", "ACT202", "BUS101", "BUS112", "BUS135", "BUS172",
            "BUS173", "BUS251", "BUS498", "FIN254", "FIN440", "INB372",
            "MGT210", "MGT212", "MGT314", "MGT321", "MGT351", "MGT368",
            "MGT489", "MIS107", "MIS207", "MKT202", "MSC301", "LAW200"
        ]
    },

    audit(transcript, waivedCourses = new Set()) {
        const creditReport = CreditCalculator.calculate(transcript);
        const gpaReport = GPACalculator.calculate(transcript, waivedCourses);

        const completedCourses = new Set();
        transcript.getUniqueCourses().forEach(code => {
            if (waivedCourses.has(code)) return;
            const best = transcript.getBestAttempt(code);
            if (best && NSUGradeSystem.isPassing(best.grade)) {
                completedCourses.add(code);
            }
        });

        const missingMandatory = this.BBA_REQ.mandatory.filter(c =>
            !completedCourses.has(c) && !waivedCourses.has(c)
        );

        const isEligible =
            creditReport.earned >= this.BBA_REQ.credits &&
            gpaReport.cgpa >= this.BBA_REQ.cgpa &&
            missingMandatory.length === 0;

        return {
            isEligible,
            creditReport,
            gpaReport,
            missingMandatory,
            retakes: transcript.getRetakenCourses()
        };
    }
};

// ==========================================
// 3. UI Logic
// ==========================================

const App = {
    transcript: new Transcript(),

    init() {
        this.cacheDOM();
        this.bindEvents();
        this.setupTabs();
    },

    cacheDOM() {
        this.els = {
            csvFile: document.getElementById('csvFile'),
            loadSampleBtn: document.getElementById('loadSampleBtn'),
            fileStatus: document.getElementById('fileStatus'),
            runAuditBtn: document.getElementById('runAuditBtn'),
            waiverInput: document.getElementById('waiverInput'),
            resultsArea: document.getElementById('resultsArea'),
            // Stats
            cgpaValue: document.getElementById('cgpaValue'),
            cgpaMeta: document.getElementById('cgpaMeta'),
            creditsValue: document.getElementById('creditsValue'),
            creditsMeta: document.getElementById('creditsMeta'),
            statusValue: document.getElementById('statusValue'),
            statusMeta: document.getElementById('statusMeta'),
            // Charts
            semesterChart: document.getElementById('semesterChart'),
            gradeChart: document.getElementById('gradeChart'),
            // Tables
            transcriptTable: document.getElementById('transcriptTable').querySelector('tbody'),
            auditSummary: document.getElementById('auditSummary'),
            deficiencies: document.getElementById('deficiencies'),
            retakes: document.getElementById('retakes')
        };
    },

    bindEvents() {
        this.els.csvFile.addEventListener('change', (e) => this.handleFileUpload(e));
        this.els.loadSampleBtn.addEventListener('click', () => this.loadSampleData());
        this.els.runAuditBtn.addEventListener('click', () => this.runAudit());
    },

    setupTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                // Add active to current
                btn.classList.add('active');
                document.getElementById(btn.dataset.tab).classList.add('active');
            });
        });
    },

    handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            this.parseCSV(event.target.result);
            this.els.fileStatus.textContent = `Loaded: ${file.name}`;
            this.els.runAuditBtn.disabled = false;
        };
        reader.readAsText(file);
    },

    loadSampleData() {
        // Sample data matching test_L3_retakes.csv content
        const csvData = `Course_Code,Credits,Grade,Semester
ENG102,3,B,Spring 2020
BUS112,3,C+,Spring 2020
ENG103,3,A-,Spring 2020
ENG105,3,B+,Summer 2020
PHI401,3,A,Summer 2020
HIS103,3,D,Summer 2020
HIS101,3,B,Fall 2020
SOC101,3,A-,Fall 2020
ENV107,3,B+,Fall 2020
PSY101,3,A,Fall 2020
BIO103,3,B,Fall 2020
HIS103,3,C+,Spring 2021
ECO101,3,F,Spring 2021
ECO104,3,B,Spring 2021
MIS107,3,B+,Summer 2021
BUS251,3,A-,Summer 2021
BUS172,3,A,Summer 2021
ECO101,3,B,Fall 2021
BUS173,3,B+,Fall 2021
BUS135,3,A-,Fall 2021
ACT201,3,C+,Spring 2022
ACT202,3,B,Spring 2022
FIN254,3,B+,Spring 2022
LAW200,3,A,Summer 2022
INB372,3,A-,Summer 2022
MKT202,3,B+,Summer 2022
MIS207,3,A,Fall 2022
MGT212,3,B,Fall 2022
MGT351,3,B+,Fall 2022
ACT201,3,B+,Spring 2023
MGT314,3,A-,Spring 2023
MGT368,3,A,Spring 2023
MGT489,3,B+,Summer 2023
MKT337,3,A,Summer 2023
MKT344,3,A-,Summer 2023
MKT460,3,A,Fall 2023
MKT470,3,A-,Fall 2023
MKT412,3,B+,Fall 2023
MKT382,3,A,Spring 2024
FIN440,3,B+,Spring 2024
MGT330,3,A-,Spring 2024
HRM370,3,B,Summer 2024`;

        this.parseCSV(csvData);
        this.els.fileStatus.textContent = "Loaded: Sample Data (Test L3)";
        this.els.runAuditBtn.disabled = false;

        // Auto-run for convenience
        this.runAudit();
    },

    parseCSV(csvText) {
        this.transcript = new Transcript();
        const lines = csvText.split('\n');

        lines.forEach(line => {
            const parts = line.split(',');
            if (parts.length >= 4 && parts[0].trim() !== 'Course_Code') {
                const record = new CourseRecord(parts[0], parts[1], parts[2], parts[3]);
                this.transcript.addRecord(record);
            }
        });

        this.renderTranscriptTable();
    },

    getWaivedCourses() {
        const input = this.els.waiverInput.value;
        if (!input) return new Set();
        return new Set(input.split(',').map(c => c.trim().toUpperCase()));
    },

    runAudit() {
        const waived = this.getWaivedCourses();
        const results = AuditCalculator.audit(this.transcript, waived);

        this.renderDashboard(results);
        this.renderAuditReport(results);
        this.els.resultsArea.classList.remove('hidden');
    },

    renderDashboard(results) {
        // Stats
        this.els.cgpaValue.textContent = results.gpaReport.cgpa.toFixed(2);
        this.els.cgpaMeta.textContent = results.gpaReport.classStanding;

        this.els.creditsValue.textContent = results.creditReport.earned.toFixed(1);
        this.els.creditsMeta.textContent = `Attempted: ${results.creditReport.attempted.toFixed(1)}`;

        this.els.statusValue.textContent = results.isEligible ? "ELIGIBLE" : "NOT ELIGIBLE";
        this.els.statusValue.style.color = results.isEligible ? "var(--success)" : "var(--danger)";
        this.els.statusMeta.textContent = results.isEligible ? "All requirements met" : "See audit for details";

        // Charts (Simple HTML Bar Charts)
        this.renderChart(this.els.gradeChart, results.gpaReport.gradeDist, null);

        // Transform Semester Data for Chart
        const semData = {};
        for (const [sem, data] of Object.entries(results.gpaReport.semesterData)) {
            if (data.credits > 0) {
                semData[sem] = (data.points / data.credits).toFixed(2);
            }
        }
        this.renderChart(this.els.semesterChart, semData, 4.0);
    },

    renderChart(container, data, maxValue) {
        container.innerHTML = '';
        const max = maxValue || Math.max(...Object.values(data));

        for (const [label, value] of Object.entries(data)) {
            const heightPct = (value / max) * 100;
            const bar = document.createElement('div');
            bar.className = 'bar';
            bar.style.height = `${heightPct}%`;
            bar.style.width = '30px';
            bar.title = `${label}: ${value}`;
            bar.setAttribute('data-value', value);

            // Label below bar could be added here

            container.appendChild(bar);
        }
    },

    renderTranscriptTable() {
        const tbody = this.els.transcriptTable;
        tbody.innerHTML = '';

        this.transcript.records.forEach(r => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${r.code}</td>
                <td>${r.credits}</td>
                <td>${r.grade}</td>
                <td>${r.semester}</td>
                <td>${r.qualityPoints.toFixed(1)}</td>
                <td>${NSUGradeSystem.isPassing(r.grade) ? 'Pass' : 'Fail'}</td>
            `;
            tbody.appendChild(row);
        });
    },

    renderAuditReport(results) {
        // Deficiencies
        let defHTML = '<h3>Deficiencies</h3>';
        if (results.isEligible) {
            defHTML += '<div class="audit-item success">✓ No deficiencies found</div>';
        } else {
            if (results.creditReport.earned < 126) {
                defHTML += `<div class="audit-item error">✗ Credits: ${results.creditReport.earned}/126 (Deficit: ${(126 - results.creditReport.earned).toFixed(1)})</div>`;
            }
            if (results.gpaReport.cgpa < 2.0) {
                defHTML += `<div class="audit-item error">✗ CGPA: ${results.gpaReport.cgpa.toFixed(2)}/2.0</div>`;
            }
            if (results.missingMandatory.length > 0) {
                defHTML += `<div class="audit-item error">✗ Missing Mandatory Courses:</div><ul>`;
                results.missingMandatory.forEach(c => defHTML += `<li>${c}</li>`);
                defHTML += `</ul>`;
            }
        }
        this.els.deficiencies.innerHTML = defHTML;

        // Retakes
        let retakeHTML = '<h3>Retaken Courses</h3>';
        const uniqueRetakes = Object.keys(results.retakes);
        if (uniqueRetakes.length === 0) {
            retakeHTML += '<div class="audit-item">No retakes found.</div>';
        } else {
            uniqueRetakes.forEach(code => {
                const history = results.retakes[code];
                retakeHTML += `<div class="audit-item"><strong>${code}</strong>: `;
                retakeHTML += history.map(h => `${h.grade} (${h.semester})`).join(' → ');
                retakeHTML += `</div>`;
            });
        }
        this.els.retakes.innerHTML = retakeHTML;
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => App.init());
