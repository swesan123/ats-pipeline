"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Loader2, Trash2, FileText, Eye, ChevronDown, Copy, AlertCircle, Plus } from "lucide-react";
import { jobsApi, skillsApi, aiSkillSuggestionsApi } from "@/lib/api";
import { ResumeGenerationWorkflow } from "@/components/resumes/ResumeGenerationWorkflow";

const updateJobSchema = z.object({
  status: z.string().optional(),
  notes: z.string().optional(),
  contact_name: z.string().optional(),
});

type UpdateJobFormValues = z.infer<typeof updateJobSchema>;

interface JobDetailsPanelProps {
  job: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate?: () => void;
  onDelete?: () => void;
}

export function JobDetailsPanel({
  job,
  open,
  onOpenChange,
  onUpdate,
  onDelete,
}: JobDetailsPanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDescription, setShowDescription] = useState(false);
  const [showMatchDetails, setShowMatchDetails] = useState(false);
  const [matchData, setMatchData] = useState<any>(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [coverLetterLoading, setCoverLetterLoading] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);
  const [showCoverLetter, setShowCoverLetter] = useState(false);
  const [showResumeWorkflow, setShowResumeWorkflow] = useState(false);
  const [addingSkills, setAddingSkills] = useState<Set<string>>(new Set());

  const form = useForm<UpdateJobFormValues>({
    resolver: zodResolver(updateJobSchema),
    defaultValues: {
      status: job?.status || "New",
      notes: job?.notes || "",
      contact_name: job?.contact_name || "",
    },
  });

  // Reset form when job changes
  useEffect(() => {
    if (job) {
      form.reset({
        status: job?.status || "New",
        notes: job?.notes || "",
        contact_name: job?.contact_name || "",
      });
    }
  }, [job, form]);

  const handleUpdate = async (data: UpdateJobFormValues) => {
    setLoading(true);
    setError(null);

    try {
      // Automatically set date_applied when status changes to "Applied"
      const updateData: any = { ...data };
      
      // Check if status is being changed TO "Applied" (not just if it's currently "Applied")
      const currentStatus = job?.status || "New";
      const newStatus = data.status || currentStatus;
      
      // If status is being changed to "Applied" and date_applied is not already set
      if (newStatus === "Applied" && currentStatus !== "Applied" && !job?.date_applied) {
        updateData.date_applied = new Date().toISOString().split("T")[0];
      }
      // If status is already "Applied" and date_applied exists, don't overwrite it
      // If status is being changed from "Applied" to something else, keep existing date_applied
      
      await jobsApi.update(job.id, updateData);
      onUpdate?.();
    } catch (err: any) {
      setError(err.message || "Failed to update job");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    setError(null);

    try {
      await jobsApi.delete(job.id);
      onDelete?.();
      onOpenChange(false);
    } catch (err: any) {
      setError(err.message || "Failed to delete job");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateResume = () => {
    setShowResumeWorkflow(true);
  };

  const handleResumeComplete = (resumeId: number) => {
    onUpdate?.();
  };

  const handleViewMatchDetails = async () => {
    if (showMatchDetails && matchData) {
      setShowMatchDetails(false);
      return;
    }

    setMatchLoading(true);
    setError(null);
    try {
      const match = await jobsApi.match(job.id);
      setMatchData(match);
      setShowMatchDetails(true);
    } catch (err: any) {
      setError(err.message || "Failed to load match details");
    } finally {
      setMatchLoading(false);
    }
  };

  const handleGenerateCoverLetter = async () => {
    if (showCoverLetter && coverLetter) {
      setShowCoverLetter(false);
      return;
    }

    setCoverLetterLoading(true);
    setError(null);
    try {
      const result = await jobsApi.generateCoverLetter(job.id);
      // Handle both response formats for backward compatibility
      setCoverLetter(result.cover_letter_text || result.cover_letter);
      setShowCoverLetter(true);
    } catch (err: any) {
      setError(err.message || "Failed to generate cover letter");
    } finally {
      setCoverLetterLoading(false);
    }
  };

  const handleCopyCoverLetter = async () => {
    if (coverLetter) {
      try {
        await navigator.clipboard.writeText(coverLetter);
      } catch (err) {
        setError("Failed to copy cover letter");
      }
    }
  };

  const handleAddMissingSkill = async (skillName: string) => {
    if (addingSkills.has(skillName)) {
      return; // Already adding this skill
    }

    setAddingSkills((prev) => new Set(prev).add(skillName));
    setError(null);

    try {
      // Classify skill category using AI
      let category = "Backend/DB"; // Default fallback
      try {
        const classification = await aiSkillSuggestionsApi.classifyCategory({ skill_name: skillName });
        category = classification.category;
      } catch (err) {
        // Use fallback category
      }

      // Add skill to user's skills list
      await skillsApi.add({
        name: skillName,
        category: category,
      });

      // Remove from missing skills display by updating matchData
      if (matchData && matchData.missing_skills) {
        setMatchData({
          ...matchData,
          missing_skills: matchData.missing_skills.filter((s: string) => s !== skillName),
        });
      }

      // Refresh job data to update match
      onUpdate?.();
    } catch (err: any) {
      setError(err.message || `Failed to add skill "${skillName}"`);
    } finally {
      setAddingSkills((prev) => {
        const next = new Set(prev);
        next.delete(skillName);
        return next;
      });
    }
  };

  if (!job) return null;

  return (
    <>
      <Drawer open={open} onOpenChange={onOpenChange}>
        <DrawerContent className="max-h-[96vh]">
          <DrawerHeader className="border-b">
            <DrawerTitle>{job.title || "Job Details"}</DrawerTitle>
            <DrawerDescription>
              {job.company} {job.location && `• ${job.location}`}
            </DrawerDescription>
          </DrawerHeader>

          <div className="overflow-y-auto px-6 py-4 space-y-6">
            {/* Error Alert */}
            {error && (
              <Alert variant="destructive" role="alert">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Job Status and Fit Score */}
            <div className="flex items-center gap-3">
              <Badge variant="outline">{job.status || "New"}</Badge>
              {job.match?.fit_score !== undefined && (
                <Badge variant="default">
                  Fit Score: {(job.match.fit_score * 100).toFixed(1)}%
                </Badge>
              )}
            </div>

            {/* Primary Actions */}
            <section aria-label="Primary actions">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Button
                  onClick={handleGenerateResume}
                  className="w-full"
                  variant="default"
                  aria-label="Generate resume for this job"
                >
                  <FileText className="h-4 w-4 mr-2" aria-hidden="true" />
                  Generate Resume
                </Button>
                <Button
                  onClick={handleViewMatchDetails}
                  className="w-full"
                  variant="outline"
                  disabled={matchLoading}
                  aria-label="View match details"
                  aria-expanded={showMatchDetails}
                >
                  {matchLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" aria-hidden="true" />
                  ) : (
                    <Eye className="h-4 w-4 mr-2" aria-hidden="true" />
                  )}
                  View Match Details
                </Button>
                <Button
                  onClick={handleGenerateCoverLetter}
                  className="w-full"
                  variant="outline"
                  disabled={coverLetterLoading}
                  aria-label="Generate cover letter"
                  aria-expanded={showCoverLetter}
                >
                  {coverLetterLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" aria-hidden="true" />
                  ) : (
                    <FileText className="h-4 w-4 mr-2" aria-hidden="true" />
                  )}
                  Generate Cover Letter
                </Button>
              </div>
            </section>

            {/* Job Description */}
            {job.description && (
              <section aria-label="Job description">
                <Collapsible open={showDescription} onOpenChange={setShowDescription}>
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      className="w-full justify-between p-0 h-auto font-semibold"
                      aria-expanded={showDescription}
                    >
                      <span>Job Description</span>
                      <ChevronDown
                        className={`h-4 w-4 transition-transform duration-200 ${
                          showDescription ? "rotate-180" : ""
                        }`}
                        aria-hidden="true"
                      />
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="mt-2">
                    <div className="text-sm text-muted-foreground bg-muted p-4 rounded-lg max-h-96 overflow-y-auto">
                      {job.description}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </section>
            )}

            {/* Match Details */}
            {showMatchDetails && matchData && (
              <section aria-label="Match analysis" className="border-t pt-4">
                <h3 className="text-lg font-semibold mb-4">Match Analysis</h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium mb-2">
                      Fit Score: {(matchData.fit_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  
                  {matchData.matching_skills && matchData.matching_skills.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">
                        Matching Skills ({matchData.matching_skills.length})
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {matchData.matching_skills.slice(0, 20).map((skill: string) => (
                          <Badge key={skill} variant="default">
                            {skill}
                          </Badge>
                        ))}
                        {matchData.matching_skills.length > 20 && (
                          <Badge variant="outline">
                            +{matchData.matching_skills.length - 20} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {matchData.missing_skills && matchData.missing_skills.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">
                        Missing Skills ({matchData.missing_skills.length})
                      </p>
                      <p className="text-xs text-muted-foreground mb-2">
                        Click on a skill to add it to your skills list
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {matchData.missing_skills.slice(0, 20).map((skill: string) => {
                          const isAdding = addingSkills.has(skill);
                          return (
                            <Badge
                              key={skill}
                              variant="destructive"
                              className="cursor-pointer hover:opacity-80 transition-opacity"
                              onClick={() => handleAddMissingSkill(skill)}
                              aria-label={`Add ${skill} to skills`}
                            >
                              {skill}
                              {isAdding ? (
                                <Loader2 className="h-3 w-3 ml-1 animate-spin" aria-hidden="true" />
                              ) : (
                                <Plus className="h-3 w-3 ml-1" aria-hidden="true" />
                              )}
                            </Badge>
                          );
                        })}
                        {matchData.missing_skills.length > 20 && (
                          <Badge variant="outline">
                            +{matchData.missing_skills.length - 20} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Cover Letter */}
            {showCoverLetter && coverLetter && (
              <section aria-label="Generated cover letter" className="border-t pt-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Generated Cover Letter</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyCoverLetter}
                    aria-label="Copy cover letter to clipboard"
                  >
                    <Copy className="h-4 w-4 mr-2" aria-hidden="true" />
                    Copy
                  </Button>
                </div>
                <div className="text-sm text-muted-foreground bg-muted p-4 rounded-lg max-h-96 overflow-y-auto whitespace-pre-wrap">
                  {coverLetter}
                </div>
              </section>
            )}

            {/* Update Form */}
            <section aria-label="Edit job information" className="border-t pt-4">
              <Form {...form}>
                <form onSubmit={form.handleSubmit(handleUpdate)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Status</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value}
                        >
                          <FormControl>
                            <SelectTrigger aria-describedby="status-description">
                              <SelectValue placeholder="Select status" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="New">New</SelectItem>
                            <SelectItem value="Interested">Interested</SelectItem>
                            <SelectItem value="Applied">Applied</SelectItem>
                            <SelectItem value="Interview">Interview</SelectItem>
                            <SelectItem value="Offer">Offer</SelectItem>
                            <SelectItem value="Rejected">Rejected</SelectItem>
                            <SelectItem value="Withdrawn">Withdrawn</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormDescription id="status-description">
                          Current status of this job application
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="notes"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Notes</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Add notes about this job..."
                            className="min-h-[100px]"
                            {...field}
                            aria-describedby="notes-description"
                          />
                        </FormControl>
                        <FormDescription id="notes-description">
                          Personal notes and observations about this position
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="contact_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Contact Name</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Recruiter name"
                            {...field}
                            aria-describedby="contact-description"
                          />
                        </FormControl>
                        <FormDescription id="contact-description">
                          Name of recruiter or hiring manager
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="flex flex-col-reverse sm:flex-row justify-between gap-3 pt-4 border-t">
                    <Button
                      type="button"
                      variant="destructive"
                      onClick={() => setShowDeleteConfirm(true)}
                      disabled={loading || showDeleteConfirm}
                      aria-label="Delete this job"
                    >
                      <Trash2 className="h-4 w-4 mr-2" aria-hidden="true" />
                      Delete Job
                    </Button>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={loading}
                      >
                        Cancel
                      </Button>
                      <Button type="submit" disabled={loading}>
                        {loading && (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                        )}
                        Save Changes
                      </Button>
                    </div>
                  </div>
                </form>
              </Form>
            </section>

            {/* Delete Confirmation */}
            {showDeleteConfirm && (
              <Alert variant="destructive" role="alertdialog" aria-live="assertive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="space-y-3">
                  <p className="font-medium">
                    Are you sure you want to delete this job? This action cannot be undone.
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowDeleteConfirm(false)}
                      disabled={loading}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleDelete}
                      disabled={loading}
                    >
                      {loading && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                      )}
                      Yes, Delete
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>
        </DrawerContent>
      </Drawer>

      {/* Resume Generation Workflow */}
      {showResumeWorkflow && (
        <ResumeGenerationWorkflow
          jobId={job.id}
          open={showResumeWorkflow}
          onOpenChange={setShowResumeWorkflow}
          onComplete={handleResumeComplete}
        />
      )}
    </>
  );
}
