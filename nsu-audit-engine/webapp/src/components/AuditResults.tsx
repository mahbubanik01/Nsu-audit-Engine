import type { AuditResponse, ExtraCourse } from '../types';
import { CheckCircle2, XCircle, AlertTriangle, Book, Calendar, Flame } from 'lucide-react';
import { cn } from '../lib/utils';

interface AuditResultsProps {
  data: AuditResponse;
}

export default function AuditResults({ data }: AuditResultsProps) {
  const { summary, deficiencies, semester_breakdown, program } = data;
  
  const progressPercent = Math.min(100, Math.round((summary.credits_earned / summary.credits_required) * 100));

  return (
    <div className="space-y-6">
      
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={cn(
          "p-6 rounded-2xl border flex items-start space-x-4 shadow-sm",
          summary.is_eligible 
            ? "bg-green-50 border-green-200 text-green-900" 
            : "bg-red-50 border-red-200 text-red-900"
        )}>
          {summary.is_eligible ? (
            <CheckCircle2 className="w-8 h-8 text-green-600 mt-1 shrink-0" />
          ) : (
            <XCircle className="w-8 h-8 text-red-600 mt-1 shrink-0" />
          )}
          <div>
            <h3 className="text-xl font-bold tracking-tight">
              {summary.is_eligible ? "Eligible to Graduate" : "Currently Ineligible"}
            </h3>
            <p className={cn(
              "font-medium text-sm mt-1",
              summary.is_eligible ? "text-green-700" : "text-red-700"
            )}>
              {program} Program • {summary.cgpa.toFixed(2)} CGPA
            </p>
          </div>
        </div>

        <div className="p-6 bg-white rounded-2xl border border-slate-200 flex flex-col justify-center shadow-sm">
          <div className="flex justify-between items-end mb-3">
            <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
              <Flame className="w-4 h-4 text-orange-400" />
              <span>Credits</span>
            </span>
            <div className="text-right">
              <span className="font-bold text-slate-900 text-xl">{summary.credits_earned} <span className="text-slate-400 text-base">/ {summary.credits_required}</span></span>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                {data.raw_records || 0} Records Parsed
              </div>
            </div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden ring-1 ring-inset ring-slate-200/50">
            <div 
              className={cn(
                "h-full rounded-full transition-all duration-1000",
                progressPercent >= 100 ? "bg-nsu-cyan" : "bg-nsu-blue"
              )}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Deficiencies */}
      {!summary.is_eligible && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-amber-900 mb-4">
            <AlertTriangle className="w-6 h-6" />
            <h3 className="font-bold text-lg">Missing Requirements</h3>
          </div>
          <div className="space-y-5">
            {deficiencies.missing_mandatory && deficiencies.missing_mandatory.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800/70 mb-2">Mandatory Core</h4>
                <div className="flex flex-wrap gap-2">
                  {deficiencies.missing_mandatory.map(course => (
                    <span key={course} className="px-3 py-1.5 bg-white border border-amber-200 text-amber-900 rounded-lg text-sm font-bold shadow-sm">
                      {course}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {deficiencies.missing_core && deficiencies.missing_core.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800/70 mb-2">Required Core</h4>
                <div className="flex flex-wrap gap-2">
                  {deficiencies.missing_core.map(course => (
                    <span key={course} className="px-3 py-1.5 bg-white border border-amber-200 text-amber-900 rounded-lg text-sm font-bold shadow-sm">
                      {course}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {deficiencies.credit_deficit > 0 && (
              <div className="text-amber-800 font-medium text-sm mt-3 pt-3 border-t border-amber-200/50">
                You are short by <strong>{deficiencies.credit_deficit}</strong> credits.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Extra / Non-Required Courses */}
      {data.extra_courses && data.extra_courses.length > 0 && (
        <div className="bg-violet-50 border border-violet-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg text-violet-900 flex items-center space-x-2">
              <Book className="w-5 h-5" />
              <span>Extra / Non-Required Courses</span>
            </h3>
            <span className="text-xs font-bold text-violet-600 bg-white border border-violet-200 px-2.5 py-1 rounded-full">
              {data.extra_courses.length} courses · {data.extra_courses.reduce((sum, c) => sum + c.credits, 0)} CR
            </span>
          </div>
          <p className="text-xs text-violet-700 mb-3 font-medium">
            These contribute to your credits and CGPA but are not part of your program requirements.
          </p>

          <div className="space-y-5">
            {Object.entries(
              data.extra_courses.reduce((acc, course) => {
                const cat = course.category || 'Other';
                (acc[cat] = acc[cat] || []).push(course);
                return acc;
              }, {} as Record<string, ExtraCourse[]>)
            ).sort().map(([category, courses]) => (
              <div key={category} className="space-y-2">
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-violet-400 px-1">
                  {category}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {courses.map(course => (
                    <div key={course.course_code} className="flex items-center space-x-2 px-3 py-2 bg-white border border-violet-100 rounded-xl shadow-sm hover:border-violet-300 transition-colors">
                      <span className="font-bold text-violet-900 text-sm">{course.course_code}</span>
                      <span className={cn(
                        "text-xs font-bold",
                        ['A','A-','B+','B'].includes(course.grade) ? 'text-green-600' : 
                        course.grade === 'F' ? 'text-red-500' : 'text-slate-600'
                      )}>
                        {course.grade}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">{course.credits}CR</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unrecognized / Invalid Courses */}
      {data.unrecognized_courses && data.unrecognized_courses.length > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg text-rose-900 flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              <span>Unrecognized / Invalid Codes</span>
            </h3>
            <span className="text-xs font-bold text-rose-600 bg-white border border-rose-200 px-2.5 py-1 rounded-full">
              {data.unrecognized_courses.length} anomalies
            </span>
          </div>
          <p className="text-xs text-rose-700 mb-3 font-medium">
            Warning: these courses do not follow standard NSU conventions (e.g. HIS5010). They may be transcription errors or non-standard electives.
          </p>
          <div className="flex flex-wrap gap-2">
            {data.unrecognized_courses.map(course => (
              <div key={course.course_code} className="flex items-center space-x-2 px-3 py-2 bg-white border border-rose-200 rounded-xl shadow-sm">
                <span className="font-bold text-rose-900 text-sm">{course.course_code}</span>
                <span className="text-xs font-bold text-rose-500">{course.grade}</span>
                <span className="text-[10px] text-slate-400 font-medium">{course.credits}CR</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Semester Breakdown */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h3 className="font-bold text-slate-800 flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-slate-400" />
            <span>Academic History</span>
          </h3>
        </div>
        <div className="divide-y divide-slate-100">
          {semester_breakdown.map((sem, i) => (
            <div key={i} className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="font-semibold text-slate-900 text-lg">{sem.semester}</span>
                <span className="text-sm font-bold text-slate-600 bg-white border border-slate-200 shadow-sm px-3 py-1 rounded-full">
                  GPA: {sem.gpa.toFixed(2)}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {sem.courses.map((course, j) => {
                  const isUnrecognized = data.unrecognized_courses?.some(u => u.course_code === course.code);
                  return (
                    <div key={j} className={cn(
                      "flex flex-row items-center justify-between p-3 rounded-xl border transition-colors relative overflow-hidden",
                      isUnrecognized 
                        ? "border-rose-400 bg-rose-50/50 hover:bg-rose-50 shadow-[0_0_8px_rgba(244,63,94,0.1)]" 
                        : "border-slate-200/60 bg-slate-50/50 hover:bg-slate-50"
                    )}>
                      {isUnrecognized && (
                        <div className="absolute top-0 right-0 px-1.5 py-0.5 bg-rose-500 text-[8px] font-black text-white uppercase tracking-tighter rounded-bl-lg">
                          Invalid
                        </div>
                      )}
                      <div className="flex items-center space-x-3">
                        <div className={cn(
                          "w-8 h-8 rounded-lg shadow-sm border flex items-center justify-center shrink-0",
                          isUnrecognized ? "bg-rose-100 border-rose-200" : "bg-white border-slate-200"
                        )}>
                          {isUnrecognized ? (
                            <AlertTriangle className="w-4 h-4 text-rose-600" />
                          ) : (
                            <Book className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                        <span className={cn(
                          "font-bold tracking-tight",
                          isUnrecognized ? "text-rose-900" : "text-slate-700"
                        )}>{course.code}</span>
                      </div>
                      <div className="text-right">
                        <div className={cn(
                          "font-extrabold text-base leading-none",
                          course.grade === 'F' ? 'text-red-500' : 
                          ['A','A-','B+','B'].includes(course.grade) ? 'text-green-600' : 'text-slate-900'
                        )}>
                          {course.grade}
                        </div>
                        <div className="text-[11px] font-semibold text-slate-400 mt-1 leading-none">{course.credits} CR</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
