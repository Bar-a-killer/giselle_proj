"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, ScrapeJob } from "@/lib/api";

const POLL_INTERVAL_MS = 3000;

export default function AddDataPage() {
  const [queriesText, setQueriesText] = useState("");
  const [depth, setDepth] = useState(5);
  const [job, setJob] = useState<ScrapeJob | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = (jobId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const updated = await api.getScrapeStatus(jobId);
      setJob(updated);
      if (updated.status === "done" || updated.status === "error") {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }, POLL_INTERVAL_MS);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const queries = queriesText
      .split("\n")
      .map((q) => q.trim())
      .filter(Boolean);
    if (queries.length === 0) return;

    setSubmitting(true);
    setSubmitError(null);
    try {
      const started = await api.startScrape(queries, { depth });
      setJob(started);
      startPolling(started.job_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 px-6 py-8">
      <div>
        <h1 className="text-xl font-semibold">Add data</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Scrapes Google Maps for the search terms below (one per line, e.g. &ldquo;ramen in
          Capitol Hill Seattle&rdquo;) and adds whatever it finds to the database. This hits real
          Google Maps pages through a headless browser, so it can take a minute or two - go slow,
          don&apos;t crank up depth/concurrency, and don&apos;t spam this if a run is already in
          progress.
        </p>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-3">
        <textarea
          value={queriesText}
          onChange={(e) => setQueriesText(e.target.value)}
          placeholder={"ramen in Capitol Hill Seattle\ncoffee in Capitol Hill Seattle"}
          rows={4}
          className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm outline-none focus:border-zinc-500 dark:border-zinc-700 dark:bg-zinc-900"
        />
        <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-300">
          Depth (how far to scroll search results; higher = more venues, slower)
          <input
            type="number"
            min={1}
            max={20}
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="w-16 rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>
        <button
          type="submit"
          disabled={submitting || job?.status === "pending" || job?.status === "running"}
          className="w-fit rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {job?.status === "running" ? "Scraping..." : "Start scrape"}
        </button>
      </form>

      {submitError && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-400">
          {submitError}
        </div>
      )}

      {job && (
        <div className="rounded-lg border border-zinc-200 px-4 py-3 text-sm dark:border-zinc-800">
          {(job.status === "pending" || job.status === "running") && (
            <p className="text-zinc-600 dark:text-zinc-300">
              {job.status === "pending" ? "Queued..." : "Running - this can take a minute or two..."}
            </p>
          )}
          {job.status === "done" && job.counts && (
            <div className="text-emerald-700 dark:text-emerald-400">
              <p className="font-medium">Done.</p>
              <p>
                {job.counts.venues_created} new venue(s) ({job.counts.venues_seen} seen),{" "}
                {job.counts.reviews_created} new review(s) ({job.counts.reviews_seen} seen).
              </p>
              <p className="mt-2">
                <Link href="/" className="underline">
                  Go browse them
                </Link>
              </p>
            </div>
          )}
          {job.status === "error" && (
            <div className="text-rose-600 dark:text-rose-400">
              <p className="font-medium">Something went wrong.</p>
              <p className="mt-1 font-mono text-xs break-words">{job.error}</p>
              {job.error?.includes("Scraper binary not found") && (
                <p className="mt-2 text-zinc-500 dark:text-zinc-400">
                  See the README for how to download the scraper binary onto the server.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
