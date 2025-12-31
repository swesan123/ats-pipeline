"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { googleSheetsApi } from "@/lib/api";

interface SyncResult {
  added?: number;
  updated?: number;
  errors?: number;
  error_details?: string[];
  sheet_name?: string;
  created?: number;
}

export function GoogleSheetsSync() {
  const [credentialsPath, setCredentialsPath] = useState("");
  const [spreadsheetUrl, setSpreadsheetUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const extractSpreadsheetId = (url: string): string | null => {
    const match = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
    if (match) {
      return match[1];
    }
    // If it's just an ID, use it directly
    if (!url.includes("/") && url.length > 10) {
      return url;
    }
    return null;
  };

  const validateInputs = (): string | null => {
    if (!credentialsPath || !spreadsheetUrl) {
      return "Please provide credentials path and spreadsheet URL";
    }

    const spreadsheetId = extractSpreadsheetId(spreadsheetUrl);
    if (!spreadsheetId) {
      return "Could not extract spreadsheet ID from URL";
    }

    return null;
  };

  const handleAction = async (actionName: string, action: 'dry-run' | 'sync' | 'push') => {
    const validationError = validateInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const spreadsheetId = extractSpreadsheetId(spreadsheetUrl);
      if (!spreadsheetId) {
        setError("Could not extract spreadsheet ID from URL");
        return;
      }

      const requestData = {
        credentials_path: credentialsPath,
        spreadsheet_url: spreadsheetUrl,
      };

      let result;
      if (action === 'dry-run') {
        result = await googleSheetsApi.syncDryRun(requestData);
      } else if (action === 'sync') {
        result = await googleSheetsApi.sync(requestData);
      } else {
        result = await googleSheetsApi.push(requestData);
      }

      setResult(result);
    } catch (err: any) {
      const errorMsg = err?.message || err?.detail || String(err) || `Failed to ${actionName}`;
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDryRun = () => handleAction("sync (dry run)", "dry-run");
  const handleSync = () => handleAction("sync", "sync");
  const handlePush = () => handleAction("push", "push");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Google Sheets Sync</CardTitle>
        <CardDescription>
          Sync jobs from Google Sheets or push jobs to Google Sheets.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Credentials Path</label>
          <Input
            placeholder="Path to Google service account JSON file"
            value={credentialsPath}
            onChange={(e) => setCredentialsPath(e.target.value)}
          />
          <p className="text-xs text-gray-500">
            Path to Google service account JSON file
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Spreadsheet Link</label>
          <Input
            placeholder="https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"
            value={spreadsheetUrl}
            onChange={(e) => setSpreadsheetUrl(e.target.value)}
          />
          <p className="text-xs text-gray-500">
            Full Google Sheets URL or just the spreadsheet ID
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <Alert>
            <CheckCircle2 className="h-4 w-4" />
            <AlertTitle>Sync Complete</AlertTitle>
            <AlertDescription>
              {result.sheet_name && (
                <p className="font-medium">Sheet used: {result.sheet_name}</p>
              )}
              {result.added !== undefined && (
                <p>Added: {result.added} jobs</p>
              )}
              {result.updated !== undefined && (
                <p>Updated: {result.updated} jobs</p>
              )}
              {result.created !== undefined && (
                <p>Created/Updated: {result.created} rows</p>
              )}
              {result.errors !== undefined && <p>Errors: {result.errors}</p>}
              {result.error_details && result.error_details.length > 0 && (
                <div className="mt-2">
                  <p className="font-medium">Error Details:</p>
                  <ul className="list-disc list-inside text-xs">
                    {result.error_details.slice(0, 10).map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                    {result.error_details.length > 10 && (
                      <li>... and {result.error_details.length - 10} more</li>
                    )}
                  </ul>
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleDryRun}
            disabled={loading}
            className="flex-1"
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sync (Dry Run)
          </Button>
          <Button
            onClick={handleSync}
            disabled={loading}
            className="flex-1"
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sync (Apply)
          </Button>
          <Button
            variant="outline"
            onClick={handlePush}
            disabled={loading}
            className="flex-1"
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Push to Sheets
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
