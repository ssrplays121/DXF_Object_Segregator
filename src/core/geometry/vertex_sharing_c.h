/* core/geometry/vertex_sharing_c.h */
#ifndef VERTEX_SHARING_C_H
#define VERTEX_SHARING_C_H

#include <stddef.h>

typedef struct {
    double x;
    double y;
} Point2D;

typedef struct {
    Point2D start;
    Point2D end;
    size_t entity_id;
} LineSegment;

typedef enum {
    LINE = 0,
    CIRCLE = 1
} EntityType;

typedef struct {
    EntityType type;
    union {
        LineSegment line;
        struct {
            Point2D center;
            double radius;
        } circle;
    } geometry;
    size_t id;
} Entity;

void spatial_hash_detection(
    Entity* entities,
    size_t num_entities,
    double tolerance,
    size_t* output_groups,
    size_t* group_sizes,
    size_t max_groups
);

#endif /* VERTEX_SHARING_C_H */
