<?php

namespace App\Http\Controllers;

use App\Http\Resources\ReviewResource;
use App\Models\Review;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class ReviewController extends Controller
{
    /**
     * Avis clients approuvés.
     * GET /api/reviews
     */
    public function index(): AnonymousResourceCollection
    {
        $reviews = Review::query()
            ->where('is_approved', true)
            ->orderBy('position')
            ->orderBy('id')
            ->get();

        return ReviewResource::collection($reviews);
    }
}
