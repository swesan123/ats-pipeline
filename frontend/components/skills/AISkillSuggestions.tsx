"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Sparkles, Plus } from "lucide-react";
import { aiSkillSuggestionsApi } from "@/lib/api";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AISkillSuggestionsProps {
  currentSkills: string[];
  onAddSkill?: (skill: string, category?: string) => void;
}

export function AISkillSuggestions({
  currentSkills,
  onAddSkill,
}: AISkillSuggestionsProps) {
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [categorizedSkills, setCategorizedSkills] = useState<Array<{skill: string, category: string}>>([]);
  const [reasoning, setReasoning] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSuggest = async () => {
    if (!jobDescription.trim()) {
      setError("Please enter a job description");
      return;
    }

    setLoading(true);
    setError(null);
    setSuggestions([]);
    setReasoning("");

    try {
      const result = await aiSkillSuggestionsApi.suggest(
        jobDescription,
        currentSkills
      );
      setSuggestions(result.suggested_skills || []);
      setCategorizedSkills(result.categorized_skills || []);
      setReasoning(result.reasoning || "");
    } catch (err: any) {
      setError(err.message || "Failed to get skill suggestions");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          AI Skill Suggestions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Paste Job Description
          </label>
          <Textarea
            placeholder="Paste the job description here to get AI-powered skill suggestions..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={6}
            className="resize-none"
          />
        </div>

        <Button
          onClick={handleSuggest}
          disabled={loading || !jobDescription.trim()}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Get Suggestions
            </>
          )}
        </Button>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {reasoning && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-sm font-medium mb-1">Why these skills?</p>
            <p className="text-sm text-gray-700">{reasoning}</p>
          </div>
        )}

        {suggestions.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Suggested Skills:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((skill, idx) => {
                const alreadyHas = currentSkills.some(
                  (s) => s.toLowerCase() === skill.toLowerCase()
                );
                const categorized = categorizedSkills.find(cs => cs.skill === skill);
                const category = categorized?.category;
                return (
                  <Badge
                    key={idx}
                    variant={alreadyHas ? "secondary" : "default"}
                    className="cursor-pointer"
                    onClick={() => !alreadyHas && onAddSkill?.(skill, category)}
                    title={category ? `Category: ${category}` : undefined}
                  >
                    {skill}
                    {category && (
                      <span className="ml-1 text-xs opacity-75">({category})</span>
                    )}
                    {!alreadyHas && (
                      <Plus className="h-3 w-3 ml-1" />
                    )}
                    {alreadyHas && (
                      <span className="ml-1 text-xs">(you have this)</span>
                    )}
                  </Badge>
                );
              })}
            </div>
            <p className="text-xs text-gray-500">
              Click on a skill badge to add it to your skills list
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
