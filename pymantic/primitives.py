__all__ = ['Triple', 'Quad', 'q_as_t', 't_as_q', 'Literal', 'NamedNode',
           'Namespace', 'BlankNode', 'Graph', 'Dataset','parse_curie', 
           'is_language', 'lang_match', 'parse_curie' ]

import collections
import datetime
from operator import itemgetter
import urllib
import urlparse

import pymantic.uri_schemes as uri_schemes

from pymantic.util import quote_normalized_iri
from pymantic.serializers import nt_escape

def is_language(lang):
    """Is something a valid XML language?"""
    if isinstance(lang, NamedNode):
        return False
    return True

def lang_match(lang1, lang2):
    """Determines if two languages are, in fact, the same language.
    
    Eg: en is the same as en-us and en-uk."""
    if lang1 is None and lang2 is None:
        return True
    elif lang1 is None or lang2 is None:
        return False
    lang1 = lang1.partition('-')
    lang2 = lang2.partition('-')
    return lang1[0] == lang2[0] and (lang1[2] == '' or lang2[2] == '' or\
                                     lang1[2] == lang2[2])

def parse_curie(curie, namespaces):
    """
    Parses a CURIE within the context of the given namespaces. Will also accept
    explicit URIs and wrap them in an rdflib URIRef.
    
    Specifically:

    1) If the CURIE is not of the form [stuff] and the prefix is in the list of
       standard URIs, it is wrapped in a URIRef and returned unchanged.
    2) Otherwise, the CURIE is parsed by the rules of CURIE Syntax 1.0:
       http://www.w3.org/TR/2007/WD-curie-20070307/ The default namespace is the
       namespace keyed by the empty string in the namespaces dictionary.
    3) If the CURIE's namespace cannot be resolved, a ValueError is raised.
    """
    definitely_curie = False
    if curie[0] == '[' and curie[-1] == ']':
        curie = curie[1:-1]
        definitely_curie = True
    prefix, sep, reference = curie.partition(':')
    if not definitely_curie:
        if prefix in uri_schemes.schemes:
            return NamedNode(curie)
    if not reference and '' in namespaces:
        reference = prefix
        return namespaces[''](reference)
    if prefix in namespaces:
        return namespaces[prefix](reference)
    else:
        raise ValueError('Could not parse CURIE prefix %s from namespaces %s' % (prefix, namespaces))

def parse_curies(curies, namespaces):
    """Parse multiple CURIEs at once."""
    for curie in curies:
        yield parse_curie(curie, namespaces)

def to_curie(uri, namespaces, seperator=":", explicit=False):
    """Converts a URI to a CURIE using the prefixes defined in namespaces. If
    there is no matching prefix, return the URI unchanged.
    
    namespaces - a dictionary of prefix -> namespace mappings.
    
    separator - the character to use as the separator between the prefix and
                the local name.
                
    explicit - if True and the URI can be abbreviated, wrap the abbreviated form
               in []s to indicate that it is definitely a CURIE."""
    for prefix, namespace in namespaces.items():
        if uri.startswith(namespace):
            if explicit:
                return '[' + uri.replace(namespace, prefix + seperator) + ']'
            else:
                return uri.replace(namespace, prefix + seperator)
    return uri



class Triple(tuple):
    'Triple(subject, predicate, object)' 

    __slots__ = () 

    _fields = ('subject', 'predicate', 'object') 

    def __new__(_cls, subject, predicate, object):
        return tuple.__new__(_cls, (subject, predicate, object)) 

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new Triple object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 3:
            raise TypeError('Expected 3 arguments, got %d' % len(result))
        return result 

    def __repr__(self):
        return 'Triple(subject=%r, predicate=%r, object=%r)' % self 

    def _asdict(t):
        'Return a new dict which maps field names to their values'
        return {'subject': t[0], 'predicate': t[1], 'object': t[2]} 

    def _replace(_self, **kwds):
        'Return a new Triple object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('subject', 'predicate', 'object'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result 

    def __getnewargs__(self):
        return tuple(self) 

    subject = property(itemgetter(0))
    predicate = property(itemgetter(1))
    object = property(itemgetter(2))
    
    def __str__(self):
        return self.subject.toNT() + ' ' + self.predicate.toNT() + ' ' + self.object.toNT() + ' .\n'
    
    def toString(self):
        return str(self)
        
class Quad(tuple):
    'Quad(subject, predicate, object, graph)'

    __slots__ = () 

    _fields = ('subject', 'predicate', 'object', 'graph')

    def __new__(_cls, subject, predicate, object, graph):
        return tuple.__new__(_cls, (subject, predicate, object, graph))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new Quad object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 4:
            raise TypeError('Expected 4 arguments, got %d' % len(result))
        return result 

    def __repr__(self):
        return 'Quad(subject=%r, predicate=%r, object=%r, graph=%r)' % self 

    def _asdict(t):
        'Return a new dict which maps field names to their values'
        return {'subject': t[0], 'predicate': t[1], 'object': t[2], 'graph': t[3],}

    def _replace(_self, **kwds):
        'Return a new Quad object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('subject', 'predicate', 'object', 'graph'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result 

    def __getnewargs__(self):
        return tuple(self) 

    subject = property(itemgetter(0))
    predicate = property(itemgetter(1))
    object = property(itemgetter(2))
    graph = property(itemgetter(3))
    
    def __str__(self):
        return str(self.subject) + ' ' + str(self.predicate) + ' ' + str(self.object) + ' ' + str(self.graph) + ' .\n'

def q_as_t(quad):
    return Triple(quad.subject, quad.predicate, quad.object)

def t_as_q(graph_name, triple):
    return Quad(triple.subject, triple.predicate, triple.object, graph_name)

class Literal(tuple):
    """Literal(value, language, datatype)""" 

    __slots__ = () 

    _fields = ('value', 'language', 'datatype') 
    
    types = {
        int: lambda v: (str(v), NamedNode('http://www.w3.org/2001/XMLSchema#integer')),
        datetime.datetime: lambda v: (v.isoformat(), NamedNode('http://www.w3.org/2001/XMLSchema#dateTime'))
    }

    def __new__(_cls, value, language=None, datatype=None):
        if not isinstance(value, str) and not isinstance(value, unicode):
            value, auto_datatype = _cls.types[type(value)](value)
            if datatype is None:
                datatype = auto_datatype
        return tuple.__new__(_cls, (value, language, datatype)) 

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new Literal object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 3:
            raise TypeError('Expected 3 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        return 'Literal(value=%r, language=%r, datatype=%r)' % self 

    def _asdict(t):
        'Return a new dict which maps field names to their values'
        return {'value': t[0], 'language': t[1], 'datatype': t[2]} 

    def _replace(_self, **kwds):                                                                            
        'Return a new Literal object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('value', 'language', 'datatype'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result 

    def __getnewargs__(self):
        return tuple(self) 

    value = property(itemgetter(0))
    language = property(itemgetter(1))
    datatype = property(itemgetter(2))
    
    interfaceName = "Literal"
    
    def __str__(self):
        return unicode(self.value)
        
    def toNT(self):
        quoted = '"' + nt_escape(self.value) + '"'
        if self.language:
            return quoted + '@' + self.language
        elif self.datatype:
            return quoted + '^^' + str(self.datatype)
        else:
            return quoted


class NamedNode(unicode):
    
    interfaceName = "NamedNode"
    
    @property
    def value(self):
        return self
        
    def __repr__(self):
        return 'NamedNode(' + self.toNT() + ')'
    
    def __str__(self):
        return self.value
    
    def toNT(self):
        return '<' + nt_escape(quote_normalized_iri(self.value)) + '>'
    

class Namespace(NamedNode):
    def __call__(self, name):
        return NamedNode(self + name)

class BlankNode(object):
    
    interfaceName = "BlankNode"

    @property
    def value(self):
        return ''.join(chr(ord(c) + 17) for c in hex(id(self))[2:])
    
    def __repr__(self):
        return 'BlankNode()'

    def __str__(self):
        return '_:' + self.value
    
    def toNT(self):
        return str(self)
    
from collections import defaultdict
def Index():
    return defaultdict(Index)

class Graph(object):
    
    def __init__(self, graph_uri=None):
        if not isinstance(graph_uri, NamedNode):
            graph_uri = NamedNode(graph_uri)
        self._uri = graph_uri
        self._triples = set()
        self._spo = Index()
        self._pos = Index()
        self._osp = Index()
        self._actions = set()
        
    @property
    def uri(self):
        return self._uri
    
    def addAction(self, action):
        self._actions.add(action)
        return self
    
    def add(self, triple):
        """Adds the specified Triple to the graph. This method returns the graph
        instance it was called on."""
        self._triples.add(triple)
        self._spo[triple.subject][triple.predicate][triple.object] = triple
        self._pos[triple.predicate][triple.object][triple.subject] = triple
        self._osp[triple.object][triple.subject][triple.predicate] = triple
        return self
        
    def remove(self, triple):
        """Removes the specified Triple from the graph. This method returns the 
        graph instance it was called on."""
        self._triples.remove(triple)
        del self._spo[triple.subject][triple.predicate][triple.object]
        del self._pos[triple.predicate][triple.object][triple.subject]
        del self._osp[triple.object][triple.subject][triple.predicate]
        return self
        
    def match(self, subject=None, predicate=None, object=None):
        """This method returns a new sequence of triples which is comprised of 
        all those triples in the current instance which match the given 
        arguments, that is, for each triple in this graph, it is included in the
        output graph, if:
        
        * calling triple.subject.equals with the specified subject as an 
        argument returns true, or the subject argument is null, AND
        * calling triple.property.equals with the specified property as an 
        argument returns true, or the property argument is null, AND
        * calling triple.object.equals with the specified object as an argument
        returns true, or the object argument is null
            
        This method implements AND functionality, so only triples matching all 
        of the given non-null arguments will be included in the result.
        """
        if subject:
            if predicate: # s, p, ???
                if object: # s, p, o
                    if Triple(subject, predicate, object) in self:
                        yield Triple(subject, predicate, object)
                else: # s, p, ?var
                    for triple in self._spo[subject][predicate].itervalues():
                        yield triple
            else: # s, ?var, ???
                if object: # s, ?var, o
                    for triple in self._osp[object][subject].itervalues():
                        yield triple
                else: # s, ?var, ?var
                    for predicate in self._spo[subject]:
                        for triple in self._spo[subject][predicate].itervalues():
                            yield triple
        elif predicate: # ?var, p, ???
            if object: # ?var, p, o
                for triple in self._pos[predicate][object].itervalues():
                    yield triple
            else: # ?var, p, ?var
                for object in self._pos[predicate]:
                    for triple in self._pos[predicate][object].itervalues():
                        yield triple
        elif object: # ?var, ?var, o
            for subject in self._osp[object]:
                for triple in self._osp[object][subject].itervalues():
                    yield triple
        else:
            for triple in self._triples:
                yield triple

    def removeMatches(self, subject, predicate, object):
        """This method removes those triples in the current graph which match 
        the given arguments."""
        for triple in self.match(subject, predicate, object):
            self.remove(triple)
        return self

    def addAll(self, graph_or_triples):
        """Imports the graph or set of triples in to this graph. This method 
        returns the graph instance it was called on."""
        for triple in graph_or_triples:
            self.add(triple)
        return self
    
    def merge(self, graph):
        """Returns a new Graph which is a concatenation of this graph and the 
        graph given as an argument."""
        new_graph = Graph()
        for triple in graph:
            new_graph.add(triple)
        for triple in self:
            new_graph.add(triple)
        return new_graph
            
    def __contains__(self, item):
        return item in self._triples
    
    def __len__(self):
        return len(self._triples)
    
    def __iter__(self):
        return iter(self._triples)
    
    def toArray(self):
        return frozenset(self._triples)

            
        

class Dataset(object):
    
    def __init__(self):
        self._graphs = defaultdict(Graph)
    
    def add(self, quad):
        self._graphs[quad.graph]._uri = quad.graph
        self._graphs[quad.graph].add(q_as_t(quad))
        
    def remove(self, quad):
        self._graphs[quad.graph].remove(q_as_t(quad))
    
    def add_graph(self, graph, named=None):
        name = named or graph.uri
        if name:
            graph._uri = name
            self._graphs[graph.uri] = graph
        else:
            raise ValueError("Graph must be named")
    
    def remove_graph(self, graph_or_uri):
        pass
    
    @property
    def graphs(self):
        return self._graphs.values()
    
    def match(self, subject=None, predicate=None, object=None, graph=None):
        if graph:
            matches = self._graphs[graph].match(subject, predicate, object)
            for match in matches:
                yield t_as_q(graph, match)
        else:
            for graph_uri, graph in self._graphs.iteritems():
                for match in graph.match(subject, predicate, object):
                    yield t_as_q(graph_uri, match)
    
    def removeMatches(self, subject=None, predicate=None, object=None, graph=None):
        """This method removes those triples in the current graph which match 
        the given arguments."""
        for quad in self.match(subject, predicate, object, graph):
            self.remove(quad)
        return self

    def addAll(self, dataset_or_quads):
        """Imports the graph or set of triples in to this graph. This method 
        returns the graph instance it was called on."""
        for quad in dataset_or_quads:
            self.add(quad)
        return self
    
    def __len__(self):
        return sum(len(g) for g in self.graphs)
    
    def __contains__(self, item):
        if hasattr(item, "graph"):
            if item.graph in self._graphs:
                graph = self._graphs[item.graph]
                return q_as_t(item) in graph
        else:
            for graph in self._graphs.itervalues():
                if item in graph:
                    return True
    
    def __iter__(self):
        for graph in self._graphs.itervalues():
            for triple in graph:
                yield t_as_q(graph.uri, triple)
    
    def toArray(self):
        return frozenset(self)

# RDF Enviroment Interfaces

class PrefixMap(dict):
    """A map of prefixes to IRIs, and provides methods to 
    turn one in to the other.
    
    Example:
    >>> prefixes = PrefixMap()
    
    Create a new prefix mapping for the prefix "rdfs"
    >>> prefixes['rdfs'] = "http://www.w3.org/2000/01/rdf-schema#"
    
    Resolve a known CURIE
    >>> prefixes.resolve("rdfs:label")
    u"http://www.w3.org/2000/01/rdf-schema#label"

    Shrink an IRI for a known CURIE in to a CURIE
    >>> prefixes.shrink("http://www.w3.org/2000/01/rdf-schema#label")
    u"rdfs:label"
    
    Attempt to resolve a CURIE with an empty prefix
    >>> prefixes.resolve(":me")
    ":me"
    
    Set the default prefix and attempt to resolve a CURIE with an empty prefix
    >>> prefixes.setDefault("http://example.org/bob#")
    >>> prefixes.resolve(":me")
    u"http://example.org/bob#me"
    """
    
    def resolve(self, curie):
        """Given a valid CURIE for which a prefix is known (for example 
        "rdfs:label"), this method will return the resulting IRI (for example 
        "http://www.w3.org/2000/01/rdf-schema#label")"""
        return parse_curie(curie, self)
    
    def shrink(self, iri):
        """Given an IRI for which a prefix is known (for example 
        "http://www.w3.org/2000/01/rdf-schema#label") this method returns a 
        CURIE (for example "rdfs:label"), if no prefix is known the original 
        IRI is returned."""
        return to_curie(iri, self)
    
    def addAll(self, other, override=False):
        if override:
            self.update(other)
        else:
            for key, value in other.iteritems():
                if key not in self:
                    self[key] = value
        return self
    
    def setDefault(self, iri):
        """Set the iri to be used when resolving CURIEs without a prefix, for 
        example ":this"."""
        self[''] = iri

class TermMap(dict):
    """A map of simple string terms to IRIs, and provides methods to turn one in
    to the other.
    
    Example:
    >>> terms = TermMap()
    
    Create a new term mapping for the term "member"
    >>> terms['member'] = "http://www.w3.org/ns/org#member"
    
    Resolve a known term to an IRI
    >>> terms.resolve("member")
    u"http://www.w3.org/ns/org#member"
    
    Shrink an IRI for a known term to a term
    >>> terms.shrink("http://www.w3.org/ns/org#member")
    u"member"
    
    Attempt to resolve an unknown term
    >>> terms.resolve("label")
    None
    
    Set the default term vocabulary and then attempt to resolve an unknown term
    >>> terms.setDefault("http://www.w3.org/2000/01/rdf-schema#")
    >>> terms.resolve("label")
    u"http://www.w3.org/2000/01/rdf-schema#label"
"""
    
    def addAll(self, other, override=False):
        if override:
            self.update(other)
        else:
            for key, value in other.iteritems():
                if key not in self:
                    self[key] = value
        return self

    def resolve(self, term):
        """Given a valid term for which an IRI is known (for example "label"), 
        this method will return the resulting IRI (for example 
        "http://www.w3.org/2000/01/rdf-schema#label").

        If no term is known and a default has been set, the IRI is obtained by 
        concatenating the term and the default iri.

        If no term is known and no default is set, then this method returns 
        null."""
        if hasattr(self, 'default'):
            return self.get(term, self.default + term)
        else:
            return self.get(term)
    
    def setDefault(self, iri):
        """The default iri to be used when an term cannot be resolved, the 
        resulting IRI is obtained by concatenating this iri with the term being 
        resolved."""
        self.default = iri
    
    def shrink(self, iri):
        """Given an IRI for which an term is known (for example 
        "http://www.w3.org/2000/01/rdf-schema#label") this method returns a 
        term (for example "label"), if no term is known the original IRI is 
        returned."""
        for term, v in self.iteritems():
            if v == iri:
                return term
        return iri
    
class Profile(object):
    def __init__(self, prefixes=None, terms=None):
        self.prefixes = prefixes or PrefixMap()
        self.terms = terms or TermMap()
    
    def resolve(toresolve):
        if ':' in toresolve:
            return self.prefixes.resolve(toresolve)
        else:
            return self.terms.resolve(toresolve)
    
    def setDefaultVocabulary(self, iri):
        self.terms.setDefault(iri)
    
    def setDefaultPrefix(self, iri):
        self.prefixes.setDefault(iri)
    
    def setTerm(self, term, iri):
        self.terms[term] = iri
    
    def setPrefix(self, prefix, iri):
        self.prefixes[prefix] = iri
    
    def importProfile(self, profile, override=False):
        self.prefixes.addAll(profile.prefixes, overide)
        self.terms.addAll(profile.terms, override)
        return self

class RDFEnvironment(Profile):
    def createBlankNode(self):
        return BlankNode()
    
    def createNamedNode(value):
        return NamedNode(value)
    
    def createLiteral(value, language=None, datatype=None):
        return Literal(value, language, datatype)
    
    def createTriple(subject, predicate, object):
        return Triple(subject, predicate, object)
    
    def createGraph(triples = tuple()):
        g = Graph()
        g.addAll(triples)
        return g
    
    def createAction(test, action):
        raise NotImplemented
    
    def createProfile(empty=False):
        if empty:
            return Profile()
        else:
            return Profile(self.prefixes, self.terms)
    
    def createTermMap(empty=False):
        if empty:
            return TermMap()
        else:
            return TermMap(self.terms)
    
    def createPrefixMap(empty=False):
        if empty:
            return PrefixMap()
        else:
            return PrefixMap(self.prefixes)
        
    # Pymantic DataSet Extensions
    
    def createQuad(subject, predicate, object, graph):
        return Quad(subject, predicate, object, graph)
    
    def createDataset(quads = tuple()):
        ds = Dataset()
        ds.addAll(quads)
        return ds
